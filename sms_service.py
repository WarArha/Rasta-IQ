def send_guardian_alert(guardian_phone, guardian_name, alert_message, simulate=True):
    """
    If simulate=True, do not send real SMS. Return SMS preview.

    Returns:
    {
        "sent": True/False,
        "mode": "simulation" or "real",
        "message": "...",
        "error": None or "..."
    }
    """
    # Safeguard against missing or empty phone number
    if not guardian_phone or not str(guardian_phone).strip():
        return {
            "sent": False,
            "mode": "simulation" if simulate else "real",
            "message": "",
            "error": "Guardian phone number is empty or invalid."
        }

    phone_clean = str(guardian_phone).strip()
    name_clean = str(guardian_name).strip() if guardian_name else "Guardian"

    if simulate:
        sms_preview = (
            f"[SIMULATED SMS to {phone_clean}]\n"
            f"Dear {name_clean},\n"
            f"{alert_message}"
        )
        return {
            "sent": True,
            "mode": "simulation",
            "message": sms_preview,
            "error": None
        }
    else:
        # Real sending mode (Not configured in hackathon MVP)
        return {
            "sent": False,
            "mode": "real",
            "message": "",
            "error": "Real SMS is not configured yet. Paid SMS gateways (like Twilio) are disabled in this MVP."
        }
