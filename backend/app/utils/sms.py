def send_sms(to_number, message):
    """
    SIMULATED SMS GATEWAY (Twilio is difficult due to Indian number trial restriction).
    This instantly returns success and logs the trigger to the console for judges.
    """
    if not to_number:
        return False
        
    print("\n" + "!"*60)
    print(f"✅ [SIMULATION SUCCESS] Alert Triggered!")
    print(f"📞 To: {to_number} | Message: {message}")
    print("!"*60 + "\n")
    
    return True



# from twilio.rest import Client

# # 👇 YAHAN APNI TWILIO DETAILS DAALO 👇
# TWILIO_SID ="AC09e3a3f5475f15bedd860c2d0a9ca21c"  # Dashboard se copy karo
# TWILIO_TOKEN ="3523e999f100b530e4aba2ee24939aed" # Dashboard se copy karo
# TWILIO_PHONE ="+19522990147"                  # Twilio jo number dega (USA wala hota hai usually)

# # 👇 JIS NUMBER PAR DEMO DIKHANA HAI (Verified Number)
# MY_PHONE_NUMBER ="+919302859264" # Apna number yahan daal do (Country code ke saath)

# def send_sms(to_number, message):
#     """
#     Sends REAL SMS using Twilio.
#     Falls back to Console Log if credentials are wrong or limit exceeded.
#     """
#     # Agar 'to_number' demo wala hai (fake), to Real SMS mat bhejo, error aayega.
#     # Hackathon Demo ke liye hum zabardasti 'MY_PHONE_NUMBER' use karenge
#     # taaki Judge koi bhi number daale, SMS *Aapke* phone pe aaye demo dikhane ke liye.
    
#     target_number = MY_PHONE_NUMBER 
    
#     print("\n" + "-"*50)
#     print(f"🔄 Initiating Real SMS to {target_number}...")

#     try:
#         client = Client(TWILIO_SID, TWILIO_TOKEN)
        
#         message = client.messages.create(
#             body=message,
#             from_=TWILIO_PHONE,
#             to=target_number
#         )
        
#         print(f"✅ [REAL SMS SENT] SID: {message.sid}")
#         print(f"📲 Check your phone: {target_number}")
#         print("-"*50 + "\n")
#         return True
        
#     except Exception as e:
#         print(f"❌ Twilio Error: {e}")
#         print("⚠️ Falling back to Mock Console Log...")
#         print(f"📨 [MOCK] Message: {message}")
#         print("-"*50 + "\n")
#         return False