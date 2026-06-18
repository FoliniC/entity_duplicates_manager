
@service
def multi_alexa_test():
    msg = "Ciao Carlo, prova di comunicazione con Echo Dot Cucina."
    
    # Tentativo 3: notify.send_message (Metodo moderno HA)
    try:
        log.error("DEBUG: Provando Test 3: notify.send_message")
        service.call("notify", "send_message", entity_id="notify.cucina_speak", message=msg)
        log.error("DEBUG: Test 3 inviato senza errori!")
    except Exception as e:
        log.error(f"DEBUG: Test 3 failed: {e}")

multi_alexa_test()
