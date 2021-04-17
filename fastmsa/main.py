from fastmsa.test import FakeConfig
from fastmsa import FastMSA
from fastmsa.api import get

config = FakeConfig()
msa = FastMSA(__name__, config)


@get("/")
def read_root():
    return {"Hello": "World"}


msa.run(reload=True)
