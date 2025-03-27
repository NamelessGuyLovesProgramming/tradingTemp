"""
Error Handler für das Trading Dashboard
"""

def handle_error(error_message):
    """
    Verarbeitet Fehlermeldungen und gibt eine benutzerfreundliche Nachricht zurück
    
    Args:
        error_message (str): Die ursprüngliche Fehlermeldung
        
    Returns:
        str: Eine benutzerfreundliche Fehlermeldung
    """
    # Bekannte Fehler abfangen und benutzerfreundliche Meldungen zurückgeben
    if "No data found" in error_message:
        return "Keine Daten für dieses Symbol gefunden. Bitte überprüfen Sie das Symbol und versuchen Sie es erneut."
    elif "Invalid symbol" in error_message:
        return "Ungültiges Symbol. Bitte geben Sie ein gültiges Aktiensymbol ein."
    elif "Connection error" in error_message:
        return "Verbindungsfehler. Bitte überprüfen Sie Ihre Internetverbindung und versuchen Sie es erneut."
    else:
        # Allgemeine Fehlermeldung für unbekannte Fehler
        return f"Ein Fehler ist aufgetreten: {error_message}"
