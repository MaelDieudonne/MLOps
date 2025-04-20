# The IMDb Reviews Tracker
This project tracks the reception of movies based on user reviews published on [IMDb](https://www.imdb.com). It was realised during the [Deployment of Data Science Projects](https://www.ensae.fr/courses/6052-mise-en-production-des-projets-de-data-science) course at ENSAE (see the [companion website](https://ensae-reproductibilite.github.io/website/)).

## :construction: Pre-Production User Management — Branch Overview

This branch hosts a pre-production version of the user management system. It is working but has not been tested extensively enough to make it into production.

It allows users to register and create an account to access the dashboard, with role-based permissions available:
- **Viewer** — limited access, read-only.
- **Admin** — full access, including user management.

Once logged in, users can update their personal information, such as their first name, last name, and password.

If you are logged in as an admin, you also have the ability to edit other users’ details — except for their passwords, which only the users themselves can change.
Test Credentials

A test account is available for demonstration purposes:
- :bust_in_silhouette: Username: `rbriggs`
- :closed_lock_with_key: Password: `def`

You can access the dashboard [here](https://test-movie-reviews-tracker.lab.sspcloud.fr/).