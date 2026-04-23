import resend

from backend.config import RESEND_API_KEY, EMAIL_FROM, BASE_URL, RESEND_TO_OVERRIDE, CONTACT_EMAIL


# -------------------
# 1. Setup
# -------------------
resend.api_key = RESEND_API_KEY


# -------------------
# 2. Send interview email
# -------------------
def send_interview_email(candidate_email: str, candidate_name: str, role: str, token: str) -> None:
    interview_link = f"{BASE_URL}/interview/{token}"

    # Resend free plan (onboarding@resend.dev) can only deliver to the
    # registered account email. Use RESEND_TO_OVERRIDE in dev/testing.
    to_address = RESEND_TO_OVERRIDE if RESEND_TO_OVERRIDE else candidate_email

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
        <h2 style="color: #1a1a2e;">Interview Invitation — {role}</h2>
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>
            Congratulations! You have been shortlisted for an AI-powered interview
            for the position of <strong>{role}</strong> at NexaraAI.
        </p>
        {"<p style='background:#fff3cd;padding:8px 12px;border-radius:6px;font-size:13px;'>📬 <em>Dev mode: original recipient was <b>" + candidate_email + "</b></em></p>" if RESEND_TO_OVERRIDE and RESEND_TO_OVERRIDE != candidate_email else ""}
        <p>Please click the button below to start your interview:</p>
        <a href="{interview_link}" style="
            display: inline-block;
            padding: 12px 28px;
            background: #6c63ff;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
        ">Start Interview</a>
        <br><br>
        <p><strong>Instructions:</strong></p>
        <ul>
            <li>Find a quiet place with a stable internet connection</li>
            <li>The interview will take approximately 20–30 minutes</li>
            <li>Answer each question honestly and clearly</li>
            <li>You can type <code>repeat</code> to hear a question again</li>
        </ul>
        <p>Interview link (copy if button doesn't work):<br>
           <a href="{interview_link}" style="color:#6c63ff;">{interview_link}</a>
        </p>
        <p>Best of luck!</p>
        <p style="color: #888;">— NexaraAI HR Team</p>
    </div>
    """

    try:
        result = resend.Emails.send({
            "from"   : EMAIL_FROM,
            "to"     : [to_address],
            "subject": f"Interview Invitation — {role} | NexaraAI",
            "html"   : html_body,
        })
        print(f"✅ Interview invite sent → {to_address} (id: {result.get('id', 'n/a')})")
    except Exception as e:
        print(f"⚠️  Email could not be sent: {e}")


# -------------------
# 3. Send offer letter
# -------------------
def send_offer_letter(candidate_email: str, candidate_name: str, role: str) -> None:
    to_address = RESEND_TO_OVERRIDE if RESEND_TO_OVERRIDE else candidate_email

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; color: #1a1a2e;">
        <div style="background: #6c63ff; padding: 24px 32px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 22px;">🎉 Offer Letter — NexaraAI</h1>
        </div>
        <div style="background: #f9f9ff; padding: 32px; border-radius: 0 0 12px 12px; border: 1px solid #e0e0f0;">
            <p>Dear <strong>{candidate_name}</strong>,</p>
            <p>
                We are delighted to inform you that after reviewing your interview performance,
                we would like to extend a formal offer for the position of
                <strong>{role}</strong> at <strong>NexaraAI</strong>.
            </p>
            <p>
                Your skills, experience, and the enthusiasm you demonstrated during the interview
                stood out to our team, and we believe you will be a great addition to NexaraAI.
            </p>
            <h3 style="color: #6c63ff;">Position Details</h3>
            <table style="width:100%; border-collapse: collapse; font-size: 14px;">
                <tr><td style="padding: 6px 0; color: #555;">Role</td><td><strong>{role}</strong></td></tr>
                <tr><td style="padding: 6px 0; color: #555;">Company</td><td><strong>NexaraAI</strong></td></tr>
                <tr><td style="padding: 6px 0; color: #555;">Type</td><td>Full-time</td></tr>
            </table>
            <br>
            <p>
                Please reply to this email to confirm your acceptance of this offer within
                <strong>5 business days</strong>.
            </p>
            <p>
                If you need any further information, please contact us at
                <a href="mailto:{CONTACT_EMAIL}" style="color: #6c63ff;">{CONTACT_EMAIL}</a>.
            </p>
            {"<p style='background:#fff3cd;padding:8px 12px;border-radius:6px;font-size:12px;'>📬 <em>Dev mode: original recipient was <b>" + candidate_email + "</b></em></p>" if RESEND_TO_OVERRIDE and RESEND_TO_OVERRIDE != candidate_email else ""}
            <br>
            <p>Warm regards,</p>
            <p><strong>HR Team</strong><br>NexaraAI<br>
               <a href="mailto:{CONTACT_EMAIL}" style="color:#6c63ff;">{CONTACT_EMAIL}</a>
            </p>
        </div>
    </div>
    """

    try:
        result = resend.Emails.send({
            "from"   : EMAIL_FROM,
            "to"     : [to_address],
            "subject": f"🎉 Offer Letter — {role} | NexaraAI",
            "html"   : html_body,
        })
        print(f"✅ Offer letter sent → {to_address} (id: {result.get('id', 'n/a')})")
    except Exception as e:
        print(f"⚠️  Offer letter could not be sent: {e}")


# -------------------
# 4. Send rejection email
# -------------------
def send_rejection_email(candidate_email: str, candidate_name: str, role: str) -> None:
    to_address = RESEND_TO_OVERRIDE if RESEND_TO_OVERRIDE else candidate_email

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; color: #1a1a2e;">
        <div style="background: #2d2d3e; padding: 24px 32px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 22px;">Interview Update — NexaraAI</h1>
        </div>
        <div style="background: #f9f9ff; padding: 32px; border-radius: 0 0 12px 12px; border: 1px solid #e0e0f0;">
            <p>Dear <strong>{candidate_name}</strong>,</p>
            <p>
                Thank you for taking the time to interview for the position of
                <strong>{role}</strong> at <strong>NexaraAI</strong>.
            </p>
            <p>
                After careful consideration, we regret to inform you that we will not
                be moving forward with your application at this time. This was a
                difficult decision, as we had many strong candidates.
            </p>
            <p>
                We appreciate the effort you put into the interview process and encourage
                you to apply for future openings that match your skills and experience.
            </p>
            <p>
                If you have any questions or would like feedback, please feel free to
                reach out to us at
                <a href="mailto:{CONTACT_EMAIL}" style="color: #6c63ff;">{CONTACT_EMAIL}</a>.
            </p>
            {"<p style='background:#fff3cd;padding:8px 12px;border-radius:6px;font-size:12px;'>📬 <em>Dev mode: original recipient was <b>" + candidate_email + "</b></em></p>" if RESEND_TO_OVERRIDE and RESEND_TO_OVERRIDE != candidate_email else ""}
            <br>
            <p>We wish you the best in your job search.</p>
            <p>Warm regards,</p>
            <p><strong>HR Team</strong><br>NexaraAI<br>
               <a href="mailto:{CONTACT_EMAIL}" style="color:#6c63ff;">{CONTACT_EMAIL}</a>
            </p>
        </div>
    </div>
    """

    try:
        result = resend.Emails.send({
            "from"   : EMAIL_FROM,
            "to"     : [to_address],
            "subject": f"Interview Update — {role} | NexaraAI",
            "html"   : html_body,
        })
        print(f"✅ Rejection email sent → {to_address} (id: {result.get('id', 'n/a')})")
    except Exception as e:
        print(f"⚠️  Rejection email could not be sent: {e}")
