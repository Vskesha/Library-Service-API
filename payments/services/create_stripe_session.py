import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_payment_session(borrowing):
    book = borrowing.book
    days = (borrowing.expected_return_date - borrowing.borrow_date).days
    total_price = int(book.daily_fee * days * 100)

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Borrowing a book: {book.title}",
                        },
                        "unit_amount": total_price,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url="http://localhost:8000/payments/success/",
            cancel_url="http://localhost:8000/payments/cancel/",  # TODO: change
        )

        return session

    except stripe.error.StripeError as e:
        raise Exception(f"Error creating stripe session: {str(e)}")
