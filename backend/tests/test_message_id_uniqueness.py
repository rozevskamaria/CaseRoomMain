from app.services.session import (
    InMemoryAttemptStore,
    RegistryCaseSource,
    SessionService,
)
from tests.test_session_service import FakeLLMClient


async def test_message_ids_unique_across_request_scoped_services():
    store = InMemoryAttemptStore()
    cases = RegistryCaseSource()
    llm = FakeLLMClient()

    def request_service():
        return SessionService(llm, store=store, cases=cases)

    proj = await request_service().start_case("xla", "practice")
    aid = proj.id
    await request_service().send_message(aid, "When did it start?")
    await request_service().append_parent_reply(aid, "It started at six months.")

    proj = await request_service()._load(aid)
    ids = [m.id for m in proj.messages]
    assert len(ids) == len(set(ids))
