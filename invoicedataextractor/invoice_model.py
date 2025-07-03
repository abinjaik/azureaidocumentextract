class InvoiceLineItem:
    def __init__(self, description=None, quantity=None, unit_price=None, total_price=None):
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price
        self.total_price = total_price

    def __repr__(self):
        return (f"InvoiceLineItem(description={self.description}, quantity={self.quantity}, "
                f"unit_price={self.unit_price}, total_price={self.total_price})")

class InvoiceData:
    def __init__(self, invoice_id=None, invoice_date=None, customer_name=None, customer_address=None,
                 vendor_name=None, vendor_address=None, total_tax=None, total_amount=None, items=None):
        self.invoice_id = invoice_id
        self.invoice_date = invoice_date
        self.customer_name = customer_name
        self.customer_address = customer_address
        self.vendor_name = vendor_name
        self.vendor_address = vendor_address
        self.total_tax = total_tax
        self.total_amount = total_amount
        self.items = items or []

    def __repr__(self):
        return (f"InvoiceData(invoice_id={self.invoice_id}, invoice_date={self.invoice_date}, "
                f"customer_name={self.customer_name}, customer_address={self.customer_address}, "
                f"vendor_name={self.vendor_name}, vendor_address={self.vendor_address}, "
                f"total_tax={self.total_tax}, total_amount={self.total_amount}, items={self.items})")