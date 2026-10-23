"""Copy/paste helper for a Kaggle notebook. Prefer reading kaggle-studio/README.md."""
import os, subprocess, sys
os.environ.setdefault('HYPIT_PROJECT_ROOT','/kaggle/working/hypit-video')
os.environ.setdefault('GRADIO_SHARE','1')
os.environ['PATH']='/kaggle/working/tools/node-v22/bin:'+os.environ.get('PATH','')
subprocess.check_call([sys.executable,'-m','pip','install','-q','-r','kaggle-studio/requirements.txt'])
print('Dependencies installed. Launch with: %run kaggle-studio/app.py')
