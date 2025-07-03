from dotenv import load_dotenv
import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
import csv
import io
from invoice_model import InvoiceData, InvoiceLineItem
import requests

load_dotenv()

AZURE_FORMRECOGNIZER_ENDPOINT = os.getenv("AZURE_FORMRECOGNIZER_ENDPOINT")
AZURE_FORMRECOGNIZER_KEY = os.getenv("AZURE_FORMRECOGNIZER_KEY")
AZURE_BLOB_CONNECTION_STRING = os.getenv("AZURE_BLOB_CONNECTION_STRING")
AZURE_BLOB_CONTAINER = "invoiceextracts"
BLOB_UPLOAD_PATH = "landing/invoices.csv"

BASE_URL =  os.getenv("S3_BASE_URL")

def clean_money(value):
    if value and isinstance(value, str):
        return value.replace("$", "").strip()
    return value

client = DocumentAnalysisClient(
    endpoint=AZURE_FORMRECOGNIZER_ENDPOINT,
    credential=AzureKeyCredential(AZURE_FORMRECOGNIZER_KEY)
)

all_rows = []
header = [
    "InvoiceId", "InvoiceDate", "CustomerName", "CustomerAddress",
    "VendorName", "VendorAddress", "TotalTax", "TotalAmount",
    "ItemDescription", "ItemQuantity", "ItemUnitPrice", "ItemTotalPrice"
]

for i in range(1, 10):
    file_name = f"batch1-{i:04d}.jpg"
    file_url = BASE_URL + file_name

    response = requests.get(file_url)
    if response.status_code == 200:
        print(f"Processing {file_name}...")
        poller = client.begin_analyze_document(
            model_id="prebuilt-invoice",
            document=response.content
        )
        result = poller.result()

        for doc in result.documents:
            def get_field(name):
                field = doc.fields.get(name)
                return field.value if field else None

            items = []
            items_field = doc.fields.get("Items")
            if items_field:
                for item in items_field.value:
                    items.append(InvoiceLineItem(
                        description=item.value.get("Description").value if item.value.get("Description") else None,
                        quantity=item.value.get("Quantity").value if item.value.get("Quantity") else None,
                        unit_price=clean_money(item.value.get("UnitPrice").value) if item.value.get("UnitPrice") else None,
                        total_price=clean_money(item.value.get("Amount").value) if item.value.get("Amount") else None,
                    ))

            invoice = InvoiceData(
                invoice_id=get_field("InvoiceId"),
                invoice_date=get_field("InvoiceDate"),
                customer_name=get_field("CustomerName"),
                customer_address=get_field("CustomerAddress"),
                vendor_name=get_field("VendorName"),
                vendor_address=get_field("VendorAddress"),
                total_amount=clean_money(str(get_field("InvoiceTotal"))),
                total_tax=clean_money(str(get_field("TotalTax"))),
                items=items
            )

            if invoice.items:
                for item in invoice.items:
                    all_rows.append([
                        invoice.invoice_id,
                        invoice.invoice_date,
                        invoice.customer_name,
                        invoice.customer_address,
                        invoice.vendor_name,
                        invoice.vendor_address,
                        clean_money(invoice.total_tax),
                        clean_money(invoice.total_amount),
                        item.description,
                        item.quantity,
                        clean_money(item.unit_price),
                        clean_money(item.total_price)
                    ])
            else:
                all_rows.append([
                    invoice.invoice_id,
                    invoice.invoice_date,
                    invoice.customer_name,
                    invoice.customer_address,
                    invoice.vendor_name,
                    invoice.vendor_address,
                    clean_money(invoice.total_tax),
                    clean_money(invoice.total_amount),
                    "", "", "", ""
                ])
    else:
        print(f"File not found or error downloading: {file_url}")

# Write all rows to a CSV in memory
output = io.StringIO()
writer = csv.writer(output)
writer.writerow(header)
writer.writerows(all_rows)
output.seek(0)

# Upload to Azure Blob Storage once
blob_service_client = BlobServiceClient.from_connection_string(AZURE_BLOB_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_BLOB_CONTAINER)
container_client.upload_blob(
    name=BLOB_UPLOAD_PATH,
    data=output.getvalue(),
    overwrite=True
)

print("Extraction completed ,Data Uploaded to Azure Storage.")