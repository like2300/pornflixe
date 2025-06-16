import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_customer(user, payment_method=None):
    customer_data = {
        "email": user.email,
        "name": f"{user.first_name} {user.last_name}",
        "metadata": {"user_id": user.id}
    }
    
    if payment_method:
        customer_data["payment_method"] = payment_method
        
    return stripe.Customer.create(**customer_data)

def create_checkout_session(customer_id, price_id, success_url, cancel_url, metadata):
    return stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata
    )