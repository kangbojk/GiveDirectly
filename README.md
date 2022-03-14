## How to use it?

1. Create a python virtual environment

`python3 -m venv .env`

2. Activate the virtual environment

`. .env/bin/activate`

3. Install required packages

`pip install -r requirements.txt`

4. Launch app

`python app.py`

## End Points

GET

* /books
* /users
* /request
* /request/{id}
* /add_books

POST
* /request
```
{"email": "hi@mars.org", "title": "alien"}
```

DELETE
* /request/{id}


## Explanation

There are 3 tables in the database, `User`, `Book` and `Loan`.

Make a GET request to `http://localhost:5000/add_books` first to populate some dummy books into DB.

When someone POST the `/request` end point with valid email address (regex`[^@]+@[^@]+\.[^@]+`), we create a new user whether the book exists or not.

If the queried book title doesn't match, we return error message. 

Otherwise, we check if there is `return_date` associated with the matched book.

If `return_date` is `None`, we return unavailable for that book, else create a new loan record and return success message.

Currently we remove loan record by making a `DELETE` request to `/request/{id}`.

The loan record will be deleted directly, we could consider to set `return_date` in `Loan` table to simulate successfully returned book.
