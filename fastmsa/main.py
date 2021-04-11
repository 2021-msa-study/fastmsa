from fastmsa.test import FakeConfig
from fastmsa import FastMsa
from fastmsa.api import get

config = FakeConfig()
msa = FastMsa(__name__, config)


@get("/")
def read_root():
    return {"Hello": "World"}


msa.run(reload=True)
