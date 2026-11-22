## Creational Design Pattern Map

### Project context
Budgeter is a local personal-finance application built with Python, Streamlit, and SQLite. It supports transaction CRUD, CSV import, income and expense tracking, category budgets, and a spending dashboard.

The assignment asks for one honest line for each of the five creational patterns: a genuine location in the system or an explanation of why there is no genuine fit.

### Singleton
No genuine fit currently. Budgeter uses a shared DATABASE_PATH configuration value, but it does not require a globally shared singleton object. Introducing one would add lifecycle complexity without solving a current problem.

### Factory Method
No genuine fit currently. The application does not currently need interchangeable object creators. Adding CSV/JSON exporters or multiple notification providers only to demonstrate Factory Method would introduce features that are not part of the current budgeting workflow.

### Abstract Factory
No genuine fit currently. Budgeter does not create families of related objects that must be switched together. Its repositories and services have specific responsibilities and no current need for interchangeable families.

### Builder
Possible future fit, but not currently justified. Builder could become useful if Budgeter needed complex report/query objects assembled from optional filters such as date range, categories, and transaction types. The current dashboard uses existing summary-service methods, so a Builder would not solve an existing problem.

### Prototype
No genuine fit currently. Budgeter does not need to clone complex preconfigured objects. Transactions and budgets are created from user input and persisted as individual records.
