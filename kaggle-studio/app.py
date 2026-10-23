from __future__ import annotations
import os, sys, json, shlex, shutil, subprocess, tempfile, time, traceback
from pathlib import Path
from typing import Optional
import gradio as gr

ROOT = Path(os.environ.get('HYPIT_PROJECT_ROOT', '/kaggle/working/hypit-video')).resolve()
ROOT.mkdir(parents=True, exist_ok=True)
ASSETS = ROOT / 'assets'; OUTPUT = ROOT / 'output'; ASSETS.mkdir(exist_ok=True); OUTPUT.mkdir(exist_ok=True)
NODE_BIN = os.environ.get('HYPIT_NODE_BIN', '/kaggle/working/tools/node-v22/bin')
if Path(NODE_BIN).exists(): os.environ['PATH'] = NODE_BIN + os.pathsep + os.environ.get('PATH','')
HYPIT = shutil.which('hypit') or os.environ.get('HYPIT_BIN', '/kaggle/working/tools/node-v22/bin/hypit')

# Only expose useful, bounded CLI operations. The arbitrary shell is intentionally not exposed.
def run_cmd(args, timeout=120):
    cmd = [str(HYPIT), *map(str,args)]
    try:
        p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout, env=os.environ.copy())
        out = (p.stdout or '') + (('\n'+p.stderr) if p.stderr else '')
        return f'$ {shlex.join(cmd)}\nExit code: {p.returncode}\n{out[-18000:]}'
    except subprocess.TimeoutExpired as e:
        return f'Command timed out after {timeout}s.\n{(e.stdout or b"").decode(errors="replace") if isinstance(e.stdout,bytes) else e.stdout or ""}'
    except Exception as e: return f'Command error: {type(e).__name__}: {e}'

def project_status():
    return json.dumps({'project_root':str(ROOT),'hypit_executable':HYPIT,'hypit_found':Path(HYPIT).exists() or shutil.which('hypit') is not None,'assets':len(list(ASSETS.iterdir())),'outputs':len(list(OUTPUT.iterdir())),'disk_free_gb':round(shutil.disk_usage(ROOT).free/1024**3,2)}, indent=2)

def save_upload(file, target_dir, stem=None):
    if not file: return None
    src = Path(file)
    ext = src.suffix.lower() or '.bin'
    name = (stem or src.stem).replace(' ','-')
    dest = target_dir / f'{name}{ext}'
    n=1
    while dest.exists():
        dest = target_dir / f'{name}-{n}{ext}'; n+=1
    shutil.copy2(src, dest)
    return dest

def upload_asset(file, kind):
    if not file: return 'Choose a file first.', None
    target = ASSETS if kind in ('Reference video','Character image','Audio','Other asset') else OUTPUT
    dest = save_upload(file,target)
    return f'Saved to `{dest}` ({dest.stat().st_size/1024**2:.2f} MB)', str(dest)

def media_probe(file_path):
    if not file_path: return 'Enter a file path or upload a reference first.'
    p=Path(file_path)
    if not p.is_absolute(): p=ROOT/p
    if not p.exists(): return f'File not found: {p}'
    return run_cmd(['media','probe',str(p)],timeout=90)

def media_frames(file_path, every, dest_name):
    p=Path(file_path)
    if not p.is_absolute(): p=ROOT/p
    if not p.exists(): return 'File not found.', None
    dest=ASSETS/(dest_name.strip() or f'frames-{int(time.time())}')
    if dest.exists(): dest=ASSETS/f'{dest.name}-{int(time.time())}'
    result=run_cmd(['media','frames',str(p),'--every',str(every),'--to',str(dest)],timeout=300)
    return result, str(dest)

def media_tile(file_path, nframes, cell, columns):
    p=Path(file_path)
    if not p.is_absolute(): p=ROOT/p
    if not p.exists(): return 'File not found.', None
    dest=ASSETS/f'contact-sheet-{int(time.time())}.jpg'
    result=run_cmd(['media','tile',str(p),'--frames',str(nframes),'--cell',str(cell),'--columns',str(columns),'--to',str(dest)],timeout=300)
    return result, str(dest) if dest.exists() else None

def status_panel():
    return project_status()+'\n\n'+run_cmd(['runtime','status'],timeout=90)+'\n\n'+run_cmd(['programs','status'],timeout=90)

def cli_action(action, extra=''):
    allowed = {
      'CLI help':['--help'], 'Runtime status':['runtime','status'], 'Programs status':['programs','status'],
      'Doctor':['doctor'], 'Project info':['project','--help'], 'Build help':['build','--help'],
      'Results list':['results','--help'], 'Auth status':['auth','status'], 'Media help':['media','--help'],
      'Runtime help':['runtime','--help'], 'Studio help':['studio','--help']
    }
    if action not in allowed: return 'Unsupported action.'
    args=allowed[action]
    if action=='Auth status' and extra.strip(): args=['auth','status',extra.strip()]
    return run_cmd(args,timeout=120)

def assistant_reply(message, history, provider, model, api_key, base_url, system_prompt):
    history = history or []
    if not message or not message.strip(): return history, ''
    user = message.strip()
    # Built-in operational commands work without any API.
    low=user.lower()
    local=None
    if low in ('status','runtime status','check status','hypit status'):
        local=status_panel()
    elif low.startswith('probe '): local=media_probe(user[6:].strip())
    elif low in ('help','hypit help','commands'):
        local=run_cmd(['--help'],timeout=60)+'\n\nUseful commands: `probe /path/video.mp4`, `runtime status`, `doctor`, `frames /path/video.mp4`, `tile /path/video.mp4`.'
    elif low.startswith('frames '):
        parts=shlex.split(user)
        if len(parts)>=2:
            res,_=media_frames(parts[1],1,'chat-frames-'+str(int(time.time())))
            local=res
    elif low.startswith('tile '):
        parts=shlex.split(user)
        if len(parts)>=2:
            res,path=media_tile(parts[1],8,320,4); local=res+(f'\nContact sheet: {path}' if path else '')
    elif low.startswith('run '):
        local='For safety, chat does not execute arbitrary shell commands. Use the Hypit Control Room action selector for supported commands.'
    if local is not None:
        history = history + [{'role':'user','content':user},{'role':'assistant','content':local}]
        return history, ''
    if not api_key:
        response=('I can run built-in Hypit status/media commands without an API key. For open-ended planning, configure an API provider in the API Settings tab.\n\n'
                  'Try: `status`, `probe /kaggle/working/hypit-video/assets/reference.mp4`, `frames /path/video.mp4`, or `tile /path/video.mp4`.')
        return history+[{'role':'user','content':user},{'role':'assistant','content':response}], ''
    try:
        system=(system_prompt or 'You are Brainrot AI Studio, a community Kaggle companion for Hypit, a practical assistant for video analysis, editing, local generation and the Hypit CLI. Give safe step-by-step instructions. Do not claim a job completed unless tool output confirms it. Explain when a feature needs an external API or local model.')
        prior=[]
        for item in history[-12:]:
            if isinstance(item,dict) and item.get('role') in ('user','assistant') and isinstance(item.get('content'),str): prior.append({'role':item['role'],'content':item['content']})
        if provider=='Google Gemini':
            from google import genai
            client=genai.Client(api_key=api_key)
            prompt=system+'\n\nConversation:\n'+ '\n'.join(f"{m['role']}: {m['content']}" for m in prior)+ '\nuser: '+user
            r=client.models.generate_content(model=model or 'gemini-3.5-flash-lite', contents=prompt)
            answer=r.text or '(The model returned no text.)'
        else:
            import requests
            url=(base_url or 'https://api.openai.com/v1').rstrip('/')+'/chat/completions'
            msgs=[{'role':'system','content':system}]+prior+[{'role':'user','content':user}]
            r=requests.post(url,headers={'Authorization':f'Bearer {api_key}','Content-Type':'application/json'},json={'model':model or 'gpt-4o-mini','messages':msgs,'temperature':0.4},timeout=120)
            r.raise_for_status(); answer=r.json()['choices'][0]['message']['content']
        history=history+[{'role':'user','content':user},{'role':'assistant','content':answer}]
        return history, ''
    except Exception as e:
        err=f'API request failed: {type(e).__name__}: {e}'
        return history+[{'role':'user','content':user},{'role':'assistant','content':err}], ''

def generate_svd(image_file, prompt, frames, steps, fps, seed, motion, out_name):
    try:
        import torch
        from PIL import Image
        from diffusers import StableVideoDiffusionPipeline
        from diffusers.utils import export_to_video
        if not image_file: return 'Upload/select a character image first.', None
        image_path=Path(image_file)
        if not image_path.exists(): return f'Image not found: {image_path}', None
        # Reuse a cached pipeline only when present in this running process.
        pipe=globals().get('_SVD_PIPE')
        if pipe is None:
            model=os.environ.get('SVD_MODEL_ID','stabilityai/stable-video-diffusion-img2vid-xt')
            pipe=StableVideoDiffusionPipeline.from_pretrained(model,torch_dtype=torch.float16,variant='fp16',low_cpu_mem_usage=True)
            pipe.enable_model_cpu_offload(); pipe.unet.enable_forward_chunking(); globals()['_SVD_PIPE']=pipe
        im=Image.open(image_path).convert('RGB'); tw,th=576,1024
        scale=max(tw/im.width,th/im.height); nw,nh=round(im.width*scale),round(im.height*scale)
        im=im.resize((nw,nh),Image.Resampling.LANCZOS); x=(nw-tw)//2; y=(nh-th)//2; im=im.crop((x,y,x+tw,y+th))
        gen=torch.Generator(device='cpu').manual_seed(int(seed))
        result=pipe(image=im,num_frames=int(frames),num_inference_steps=int(steps),fps=int(fps),motion_bucket_id=int(motion),noise_aug_strength=0.02,generator=gen)
        name=(out_name or 'generated-video').strip().replace(' ','-')
        if not name.lower().endswith('.mp4'): name+='.mp4'
        dest=OUTPUT/name; idx=1
        while dest.exists(): dest=OUTPUT/f'{Path(name).stem}-{idx}.mp4'; idx+=1
        export_to_video(result.frames[0],str(dest),fps=int(fps))
        return f'VIDEO_GENERATION_OK\nSaved: {dest}\nFrames: {len(result.frames[0])}\nDuration: {len(result.frames[0])/int(fps):.2f}s\nSize: {dest.stat().st_size/1024**2:.2f} MB\n\nNote: SVD is image-to-video. The prompt field is retained for workflow notes; SVD-XT does not follow text prompts directly.',str(dest)
    except Exception as e:
        return f'Generation failed: {type(e).__name__}: {e}\n\n{traceback.format_exc()[-5000:]}',None

def list_files():
    rows=[]
    for folder in (ASSETS,OUTPUT):
        for p in sorted(folder.rglob('*')):
            if p.is_file(): rows.append([str(p.relative_to(ROOT)),round(p.stat().st_size/1024**2,2),time.strftime('%Y-%m-%d %H:%M',time.localtime(p.stat().st_mtime))])
    return rows

with gr.Blocks(title='Brainrot AI Studio | Hypit Companion') as demo:
    gr.Markdown('# 🎬 Brainrot AI Studio\nCommunity-built Kaggle browser companion for Hypit. Media analysis, local generation and configurable AI APIs run from your notebook. Hypit attribution and its original license are retained.', elem_id='hero')
    with gr.Row():
        project_box=gr.Code(value=project_status(),label='Workspace & storage',language='json',interactive=False)
        refresh=gr.Button('Refresh workspace status',variant='secondary')
    refresh.click(project_status,outputs=project_box)
    with gr.Tabs():
        with gr.Tab('💬 Studio Chat'):
            gr.Markdown('Ask for a workflow, or use built-in commands such as `status`, `probe /path/video.mp4`, `frames /path/video.mp4`, and `tile /path/video.mp4`. API settings are in the API Settings tab.')
            chatbot=gr.Chatbot(label='Hypit assistant',height=470)
            with gr.Row():
                chat_input=gr.Textbox(placeholder='e.g. Analyze my reference video and plan a 9:16 recreation…',show_label=False,scale=8)
                send=gr.Button('Send',variant='primary',scale=1)
            clear=gr.Button('Clear chat',size='sm')
            provider_state=gr.State('Google Gemini')
            model_state=gr.State('gemini-3.5-flash-lite')
            key_state=gr.State('')
            url_state=gr.State('https://api.openai.com/v1')
            system_state=gr.State('')
            send.click(assistant_reply,[chat_input,chatbot,provider_state,model_state,key_state,url_state,system_state],[chatbot,chat_input])
            chat_input.submit(assistant_reply,[chat_input,chatbot,provider_state,model_state,key_state,url_state,system_state],[chatbot,chat_input])
            clear.click(lambda: [],outputs=chatbot)
        with gr.Tab('📁 Assets & Reference Lab'):
            with gr.Row():
                file_upload=gr.File(label='Upload reference video, character image, audio or asset',file_count='single',type='filepath')
                asset_kind=gr.Dropdown(['Reference video','Character image','Audio','Other asset'],value='Reference video',label='Asset type')
            save_btn=gr.Button('Save into project assets',variant='primary')
            save_result=gr.Markdown()
            saved_path=gr.Textbox(label='Saved path',interactive=False)
            save_btn.click(upload_asset,[file_upload,asset_kind],[save_result,saved_path])
            gr.Markdown('### Probe a video')
            probe_path=gr.Textbox(value=str(ASSETS/'reference.mp4'),label='Video path')
            probe_btn=gr.Button('Probe metadata')
            probe_out=gr.Code(label='Probe output',language='shell')
            probe_btn.click(media_probe,probe_path,probe_out)
            with gr.Row():
                frames_every=gr.Slider(1,5,value=1,step=1,label='Extract every N seconds')
                frames_name=gr.Textbox(value='reference-frames',label='New frames folder name')
            frames_btn=gr.Button('Extract frames')
            frames_out=gr.Code(label='Frame extraction output',language='shell')
            frames_saved=gr.Textbox(label='Frames folder')
            frames_btn.click(media_frames,[probe_path,frames_every,frames_name],[frames_out,frames_saved])
            with gr.Row():
                nframes=gr.Slider(4,24,value=8,step=1,label='Contact sheet frame count')
                cell=gr.Slider(160,640,value=320,step=32,label='Cell size')
                cols=gr.Slider(2,6,value=4,step=1,label='Columns')
            tile_btn=gr.Button('Build contact sheet')
            tile_out=gr.Code(label='Contact sheet output',language='shell')
            tile_image=gr.Image(label='Contact sheet preview',type='filepath')
            tile_btn.click(media_tile,[probe_path,nframes,cell,cols],[tile_out,tile_image])
        with gr.Tab('✨ Local Image-to-Video'):
            gr.Markdown('SVD-XT image-to-video, if Diffusers and the model are installed in this Kaggle session. It animates a still image; it does **not** reproduce reference-video motion exactly or directly obey text prompts.')
            character_file=gr.File(label='Character / start image',type='filepath',file_count='single')
            gen_prompt=gr.Textbox(label='Creative brief (saved as notes only for SVD-XT)',lines=3,placeholder='Describe intended motion, camera, mood…')
            with gr.Row():
                gen_frames=gr.Slider(8,25,value=14,step=1,label='Frames')
                gen_steps=gr.Slider(5,25,value=10,step=1,label='Inference steps (10 is faster)')
                gen_fps=gr.Slider(5,12,value=7,step=1,label='FPS')
            with gr.Row():
                gen_seed=gr.Number(value=42,precision=0,label='Seed')
                gen_motion=gr.Slider(1,255,value=80,step=1,label='Motion bucket')
                gen_name=gr.Textbox(value='generated-video',label='Output filename')
            gen_btn=gr.Button('Generate MP4',variant='primary')
            gen_status=gr.Code(label='Generation log',language='shell')
            gen_video=gr.Video(label='Generated MP4',format='mp4')
            gen_btn.click(generate_svd,[character_file,gen_prompt,gen_frames,gen_steps,gen_fps,gen_seed,gen_motion,gen_name],[gen_status,gen_video])
        with gr.Tab('🧰 Hypit Control Room'):
            action=gr.Dropdown(['CLI help','Runtime status','Programs status','Doctor','Project info','Build help','Results list','Auth status','Media help','Runtime help','Studio help'],value='Runtime status',label='Supported Hypit command')
            extra=gr.Textbox(label='Optional endpoint for Auth status',placeholder='e.g. hypihub.default')
            run_btn=gr.Button('Run command',variant='primary')
            cmd_out=gr.Code(label='Command output',language='shell')
            run_btn.click(cli_action,[action,extra],cmd_out)
            gr.Markdown('Advanced generation and editing remain available through the full Hypit CLI. This UI intentionally does not expose arbitrary shell execution.')
        with gr.Tab('🔑 API Settings'):
            gr.Markdown('API keys are kept in this running browser session state and are not written to the repository. Use your own provider key and check provider pricing/quotas. Do not commit keys to GitHub.')
            provider=gr.Radio(['Google Gemini','OpenAI-compatible API'],value='Google Gemini',label='Provider')
            model=gr.Textbox(value='gemini-3.5-flash-lite',label='Model ID')
            api_key=gr.Textbox(label='API key',type='password')
            base_url=gr.Textbox(value='https://api.openai.com/v1',label='OpenAI-compatible base URL')
            system_prompt=gr.Textbox(label='Assistant system instructions',lines=4,value='You are Brainrot AI Studio, a community Kaggle companion for Hypit, a practical assistant for video analysis, editing, local generation and the Hypit CLI. Be explicit about which operations are real versus advice. Never claim generation completed without output verification.')
            save_api=gr.Button('Apply settings to chat',variant='primary')
            api_notice=gr.Markdown()
            save_api.click(lambda p,m,k,u,s: (p,m,k,u,s,'Settings applied to this running session. API key is not written to disk.'),[provider,model,api_key,base_url,system_prompt],[provider_state,model_state,key_state,url_state,system_state,api_notice])
        with gr.Tab('📦 Output Gallery'):
            files_btn=gr.Button('Refresh files')
            files_table=gr.Dataframe(headers=['Relative path','MB','Modified'],datatype=['str','number','str'],interactive=False)
            files_preview=gr.Textbox(label='Select a relative path and preview/download from the file browser below')
            file_preview_btn=gr.Button('Show selected file path')
            file_link=gr.File(label='File')
            files_btn.click(list_files,outputs=files_table)
            file_preview_btn.click(lambda rel: str((ROOT/rel).resolve()) if rel and (ROOT/rel).resolve().is_file() and str((ROOT/rel).resolve()).startswith(str(ROOT)) else None,files_preview,file_link)
    gr.Markdown('**Kaggle note:** the public share URL is temporary and works only while this notebook session is running. Save generated MP4s under `output/` and download them or publish notebook outputs before the session expires.')

if __name__ == '__main__':
    share = os.environ.get('GRADIO_SHARE','1') == '1'
    demo.launch(server_name='0.0.0.0',server_port=int(os.environ.get('PORT','7860')),share=share,show_error=True,theme=gr.themes.Soft(),css='''.gradio-container {max-width: 1500px !important}
#hero {padding:22px;border-radius:18px;background:linear-gradient(120deg,#17182c,#293b59 60%,#3a2754);color:white;margin-bottom:12px}
#hero h1 {font-size:30px;margin:0 0 6px 0}
#hero p {opacity:.88;margin:0}
''')
