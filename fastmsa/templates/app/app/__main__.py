from fastmsa.command import FastMSACommand


cmd = FastMSACommand()
msa = cmd.init_app()
app = msa.app


def main():
    cmd = FastMSACommand()
    cmd.run()


if __name__ == "__main__":
    main()
