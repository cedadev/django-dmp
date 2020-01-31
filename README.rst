=====
dmp
=====

dmp is a Django app to facilitate data management projects.

Quick start
-----------

1. Build the dmp pip installable from the source code::

   python setup.py sdist (from inside the django-dmp directory)

2. Install the dmp into your virtual env::

   pip install --user django-dmp/dist/django-dmp-0.1.tar.gz

3. Add "dmp" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = (
        ...
        'dmp',
    )

4. Include the 'dmp' URLconf in your project urls.py like this::

    url(r'^dmp/', include('dmp.urls')),

5. Run `python manage.py migrate` to create the dmp models.

6. Start the development server and visit http://127.0.0.1:8000/admin/
   to launch cedainfo admin interface (you'll need the Admin app enabled).

