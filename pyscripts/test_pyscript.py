"""
Test pyscript
"""
@time_trigger("startup")
def test_startup():
    log.info("Pyscript test startup triggered")

@time_trigger("cron(* * * * *)")
def test_cron():
    log.info("Pyscript test cron triggered")