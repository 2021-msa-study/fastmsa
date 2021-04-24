from fastmsa import FastMSA
from fastmsa.api import get
from fastmsa.test import FakeConfig

config = FakeConfig()
msa = FastMSA(__name__, config)


@get("/")
def read_root():
    return {"Hello": "World"}


msa.run(reload=True)
