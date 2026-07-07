"""
=========================================================
Synthetic ERP Data Generator
Deloitte Forensic Investigation Workbench
=========================================================
"""

from pathlib import Path
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

from config import DATA_DIR, DATA_CONFIG

fake = Faker()
random.seed(42)
np.random.seed(42)


def ensure_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def employee_master():
    records = []

    for i in range(DATA_CONFIG["employees"]):

        records.append({
            "employee_id": f"EMP{i+1:04}",
            "employee_name": fake.name(),
            "department": random.choice([
                "Procurement",
                "Finance",
                "Operations",
                "Legal",
                "Compliance"
            ]),
            "region": random.choice([
                "APAC",
                "EMEA",
                "AMER",
                "India"
            ]),
            "designation": random.choice([
                "Manager",
                "Senior Manager",
                "Director",
                "Analyst"
            ])
        })

    df = pd.DataFrame(records)
    df.to_csv(DATA_DIR / "employee_master.csv", index=False)
    return df


def vendor_master():

    vendors = []

    bank_accounts = []

    for i in range(DATA_CONFIG["vendors"]):

        account = f"1000{random.randint(100000,999999)}"

        bank_accounts.append(account)

        vendors.append({

            "vendor_id": f"V{i+1:05}",

            "vendor_name": fake.company(),

            "bank_account": account,

            "country": random.choice([
                "India",
                "Singapore",
                "Germany",
                "USA",
                "UK"
            ]),

            "vendor_type": random.choice([
                "Consulting",
                "IT",
                "Industrial",
                "Services"
            ])

        })

    df = pd.DataFrame(vendors)
    df.to_csv(DATA_DIR / "vendor_master.csv", index=False)

    return df


def invoices(vendors):

    invoices = []

    start = datetime.today() - timedelta(days=730)

    for i in range(DATA_CONFIG["invoices"]):

        vendor = vendors.sample(1).iloc[0]

        amount = random.randint(5000,150000)

        invoices.append({

            "invoice_id": f"INV{i+1:07}",

            "vendor_id": vendor.vendor_id,

            "invoice_date": start + timedelta(
                days=random.randint(0,730)
            ),

            "invoice_amount": amount,

            "currency":"USD"

        })

    df = pd.DataFrame(invoices)
    df.to_csv(DATA_DIR/"invoice_header.csv",index=False)

    return df


def payments(invoice_df):

    rows=[]

    for _,inv in invoice_df.iterrows():

        rows.append({

            "payment_id":fake.uuid4()[:12],

            "invoice_id":inv.invoice_id,

            "payment_amount":inv.invoice_amount,

            "payment_date":pd.to_datetime(
                inv.invoice_date
            )+timedelta(
                days=random.randint(5,45)
            )

        })

    df=pd.DataFrame(rows)

    df.to_csv(
        DATA_DIR/"payments.csv",
        index=False
    )

    return df


def approvals(invoice_df, employees):

    logs=[]

    for _,row in invoice_df.iterrows():

        emp=employees.sample(1).iloc[0]

        logs.append({

            "invoice_id":row.invoice_id,

            "approver":emp.employee_id,

            "approval_status":"Approved",

            "approval_date":
            pd.to_datetime(row.invoice_date)+timedelta(days=2)

        })

    df=pd.DataFrame(logs)

    df.to_csv(
        DATA_DIR/"approval_logs.csv",
        index=False
    )

    return df


def communications(vendors):

    keywords=[
        "urgent payment",
        "invoice",
        "approval",
        "vendor",
        "bank details",
        "Q4",
        "consulting"
    ]

    rows=[]

    for i in range(DATA_CONFIG["emails"]):

        vendor=vendors.sample(1).iloc[0]

        rows.append({

            "email_id":f"MAIL{i+1:05}",

            "vendor_id":vendor.vendor_id,

            "subject":fake.sentence(),

            "body":
            fake.paragraph()+" "+random.choice(keywords),

            "date":
            fake.date_between(
                start_date="-2y",
                end_date="today"
            )

        })

    df=pd.DataFrame(rows)

    df.to_csv(
        DATA_DIR/"emails.csv",
        index=False
    )

    return df


def main():

    ensure_dir()

    employees=employee_master()

    vendors=vendor_master()

    invoice_df=invoices(vendors)

    payments(invoice_df)

    approvals(invoice_df,employees)

    communications(vendors)

    print("Synthetic ERP data generated successfully.")


if __name__=="__main__":

    main()