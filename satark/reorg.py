import os
import shutil
import time

base = r"c:\Users\Rishabh Kumar\DatabricksHackthon\satark"

def safe_reorg():
    backend = os.path.join(base, "backend")
    api = os.path.join(base, "api")
    
    # 1. Copy backend to api
    if os.path.exists(backend):
        print(f"Copying {backend} to {api}...")
        try:
            if os.path.exists(api):
                shutil.rmtree(api)
            shutil.copytree(backend, api)
        except Exception as e:
            print(f"Error copying: {e}")
            return
            
    # 2. Rename main.py to index.py
    main_py = os.path.join(api, "main.py")
    index_py = os.path.join(api, "index.py")
    if os.path.exists(main_py):
        print(f"Renaming {main_py} to {index_py}...")
        if os.path.exists(index_py):
            os.remove(index_py)
        os.rename(main_py, index_py)
        
    # 3. Copy requirements
    root_reqs = os.path.join(os.path.dirname(base), "requirements.txt")
    satark_reqs = os.path.join(base, "requirements.txt")
    if os.path.exists(root_reqs):
        print(f"Copying {root_reqs} to {satark_reqs}...")
        shutil.copy2(root_reqs, satark_reqs)
        
    # 4. Try to delete backend (optional, won't block)
    try:
        shutil.rmtree(backend, ignore_errors=True)
    except:
        pass

if __name__ == "__main__":
    safe_reorg()
