class ApplicationProvider:
    name="base"
    def can_submit(self,job): return False
    def submit(self,job,material):
        raise NotImplementedError

class AuthorizedProvider(ApplicationProvider):
    name="authorized_provider"
    def can_submit(self,job):
        return bool(job.get("authorized_provider",False))
    def submit(self,job,material):
        # Replace only with a real authorized integration and its documented API contract.
        return {"status":"AUTOMATION_UNAVAILABLE","reason":"Authorized provider is not configured."}

class ProviderRegistry:
    def __init__(self): self.providers=[AuthorizedProvider()]
    def select(self,job):
        return next((p for p in self.providers if p.can_submit(job)),None)
