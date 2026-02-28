import random
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from config import get_db
from services.log_service import log_event

db = get_db()

# ─── Load email credentials from environment ───────────────────────────────
SMTP_EMAIL    = os.environ.get("EMAIL_ADDRESS", "")
SMTP_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")


# ─── Send OTP email via Gmail SMTP ─────────────────────────────────────────
def send_otp_email(to_email: str, otp: str) -> bool:
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"[EMAIL NOT CONFIGURED] OTP for {to_email}: {otp}")
        return False

    subject = "BIOGUARD AI — Your Login Verification Code"

    plain = f"""
Your BIOGUARD AI verification code is:

  {otp}

This code expires in 5 minutes.
If you did not request this, please ignore this email.
"""

    html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#050a0f;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#050a0f;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0"
               style="background:#0d1e2e;border-radius:16px;border:1px solid #0c2a3d;overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#0a1a2e,#0d2640);
                        padding:28px 36px;border-bottom:1px solid #0c2a3d;">
              <span style="font-size:22px;font-weight:800;letter-spacing:4px;
                           color:#ffffff;text-transform:uppercase;">
                &#11041; BIOGUARD <span style="color:#00c8ff;">AI</span>
              </span>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:36px;">
              <p style="color:#7a9db8;font-size:14px;margin:0 0 8px;">Security Alert</p>
              <h2 style="color:#e8f4ff;font-size:22px;margin:0 0 20px;">Your Verification Code</h2>
              <p style="color:#7a9db8;font-size:14px;line-height:1.6;margin:0 0 28px;">
                A login attempt was detected that requires additional verification.
                Use the code below to complete your sign-in.
              </p>

              <!-- OTP Box -->
              <div style="background:#0a1520;border:1px solid #0c2a3d;
                          border-radius:12px;padding:24px;text-align:center;margin-bottom:28px;">
                <p style="color:#7a9db8;font-size:11px;letter-spacing:3px;
                           text-transform:uppercase;margin:0 0 12px;">One-Time Password</p>
                <span style="font-size:42px;font-weight:800;letter-spacing:10px;
                             color:#00c8ff;font-family:'Courier New',monospace;">{otp}</span>
                <p style="color:#3d6680;font-size:12px;margin:12px 0 0;">
                  Expires in <strong style="color:#ffb800;">5 minutes</strong>
                </p>
              </div>

              <p style="color:#3d6680;font-size:12px;line-height:1.6;margin:0;">
                If you did not attempt to log in, your account may be at risk.
                Please change your password immediately.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#080f18;padding:20px 36px;
                        border-top:1px solid #0c2a3d;text-align:center;">
              <p style="color:#3d6680;font-size:11px;margin:0;">
                BIOGUARD AI &middot; Biometric Authentication System<br/>
                This is an automated message &mdash; do not reply.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"BIOGUARD AI <{SMTP_EMAIL}>"
        msg["To"]      = to_email

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html,  "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())

        print(f"[EMAIL SENT] OTP sent to {to_email}")
        return True

    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        print(f"[FALLBACK] OTP for {to_email}: {otp}")
        return False


# ─── Generate & send OTP ───────────────────────────────────────────────────
def generate_otp(user_id, email):
    otp = str(random.randint(100000, 999999))
    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

    db.reference("otps").child(user_id).set({
        "otp": otp,
        "expires_at": expiry.isoformat()
    })

    send_otp_email(email, otp)
    log_event(user_id, email, "OTP_GENERATED", "SUCCESS")

    return otp


# ─── Verify OTP ────────────────────────────────────────────────────────────
def verify_otp(user_id, entered_otp):
    otp_data = db.reference("otps").child(user_id).get()

    if not otp_data:
        return False

    if otp_data["otp"] != entered_otp:
        return False

    if datetime.datetime.utcnow() > datetime.datetime.fromisoformat(otp_data["expires_at"]):
        return False

    db.reference("otps").child(user_id).delete()
    return True