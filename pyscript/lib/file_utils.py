# fix_duplicates_entities
def write_yaml_standard(path, content):
    """Funzione Python standard per scrivere file, chiamata via task.executor."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        return str(e)