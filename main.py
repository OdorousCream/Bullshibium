from Interface import Interface
from NameDB.NameDB import create_db

def main():
    create_db()
    interface = Interface()
    interface.start()

if __name__ == "__main__":
    main()