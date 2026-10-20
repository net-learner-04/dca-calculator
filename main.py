from config import create_default_json, load_config
import os


def main():
    if not(os.path.exists("config.json")):
        create_default_json()
    
    data = load_config()
    
    

if __name__ == "__main__":
    main()