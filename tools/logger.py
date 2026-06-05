
import time


def log(Task):
    print("Logging: Email processed successfully.")
    print("Log Entry:",time.time())
    print("Email Text: ", Task.email_text)
    print("Classification: ", Task.classification)
    print("Generated Reply: ", Task.reply)
    print("End of log entry.\n")
