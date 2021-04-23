from fastmsa.command import FastMSACommand
from fastmsa.api import app


cmd = FastMSACommand()
msa = cmd.init_app()

if __name__ == "__main__":
    cmd.run()
