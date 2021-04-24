from fastmsa.command import FastMSACommand

cmd = FastMSACommand()
msa = cmd.init_app()

if __name__ == "__main__":
    cmd.run()
