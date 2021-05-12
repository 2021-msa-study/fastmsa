import asyncio

from fastmsa.api import app  # noqa
from fastmsa.command import FastMSACommand

cmd = FastMSACommand()
msa = cmd.init_app()


@app.on_event("startup")
async def initial_task():
    if msa.allow_external_event:
        asyncio.create_task(msa.broker.main())


if __name__ == "__main__":
    cmd.run()
