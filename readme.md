# delvarg-fullstack-website
Project files of a full stack website for Delvarg, a Venezuelan business. The website is being developed using Python, Flask, SQL Alchemy, Jinja, HTML, CSS, Bootstrap, JavaScript and jQuery.

Archivos de proyecto de un sitio web full stack para Delvarg, una empresa venezolana. El sitio web se está desarrollando utilizando Python, Flask, SQL Alchemy, Jinja, HTML, CSS, Bootstrap, JavaScript y jQuery.


Para ser capaz de correr apropiadamente esta aplicación necesitaras instalar ciertas dependencias:

  -Python (https://www.python.org/downloads/)
  
  -Flask (Entra en la terminal de Windows o VScode y escribe 'pip install flask')
  
  -Flask Login (Entra en la terminal de Windows o VScode y escribe 'pip install flask-login')
  
  -La implementación de SQL Alchemy en Flask (Entra en la terminal de Windows o VScode y escribe 'pip install flask-sqlalchemy')

  -El SDK de PayPal para manejar transacciones (Entra en la terminal de Windows o VScode y escribe 'pip install paypalrestsdk')


Una vez hecho todo esto abre el archivo "main.py" y correlo. 

Ahora abre la dirección 'http://127.0.0.1:5000/' en tu navegador y disfruta de nuestra pagina web!


En esta versión de la pagina web ya hay algunos productos agregados a la base de datos ademas de un usuario administrador:

  -correo: admin@gmail.com

  -contraseña: 1234


Si quieres experimentar un poco con una base de datos vacia encuentra en "__init__.py" la linea 22 donde dice "db.create_all()". Simplemente cambia "create" a "drop", para que ahora el codigo sea "db.drop_all()". Guarda el archivo mientras la aplicación esta corriendo, espera unos segundos, cambialo a estado original con "db.create_all()" y guarda denuevo. 

Con esto la base de datos es creada desde cero. Ten en cuenta que el primero usuario creado siempre sera el administrador.
