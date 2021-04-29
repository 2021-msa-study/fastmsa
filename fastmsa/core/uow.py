"""UnitOfWork 패턴 모듈.

UoW 는 영구 저장소의 유일한 진입점이며, 로드된 객체의 최신 상태를 계속 트래킹 합니다.
이를 통해 얻을 수 있는 3가지 이득은 다음과 같습니다.

- A *stable snapshot of the database* to work with, so the objects
  we use aren’t changing halfway through an operation
- A way to persist all of our *changes at once*, so if something goes wrong,
  we don’t end up in an inconsistent state
- A *simple API* to our persistence concerns and a handy place to get a repository
"""
