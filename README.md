# Apache Airflow course from GridU
Course contains small tasks for each element Airflow.

## Task 1. DAG creation (Part I)

**Steps:**

1. Create `jobs_dag.py` file.

2. In `jobs_dag.py` file define Python dict with params for each DAG, for example:

```config = {
'dag_id_1': {'schedule_interval': "", "start_date": datetime(2018, 11, 11)},  
'dag_id_2': {'schedule_interval': "", "start_date": datetime(2018, 11, 11)},  
'dag_id_3': {'schedule_interval': "", "start_date": datetime(2018, 11, 11)}}
```

This config should contain:

- your own **dag_id** (remember, that they must be unique for each DAG),
- **schedule_interval**: each DAG must have its own **schedule_interval**. This param has a default setting: schedule every 15 minutes, so if you don’t want your DAG to run each 15 minutes, set it to None. None is used when you only want to trigger dags manually. Note that None here is not a string “None” but rather a Python NoneType object.
- **start_date** for each DAG

3. After that, you need to iterate through config (for example with ‘for dict in config‘) and generate DAGs in the loop

## Task 2. DAG creation (Part II)

**Steps:**

Modify code to create 3 DAGs that run 3 tasks, and depend on each other as `1 >> 2 >> 3` (1 - start first) :

1. Print the following information information into log: `"{dag_id} start processing tables in database: {database}"` (use PythonOperator for that)
2. Add a dummy task (with DummyOperator) to mock insertion of a new row into DB. Suggested task id is `"insert_new_row"`
3. Add a dummy task (with DummyOperator) to mock table query. Suggested task id is `"query_the_table"`

As the DAGs being created will each work with its own table, unique table names must be set and recorded in parameters dict.

For example,

```
config = {
'dag_id_1': {'schedule_interval': "",
"start_date": datetime(2018, 11, 11),
"table_name": "table_name_1"},  
'dag_id_2': {'schedule_interval': "",
"start_date": datetime(2018, 11, 11)
"table_name": "table_name_2"},  
'dag_id_3':{'schedule_interval': "",
"start_date": datetime(2018, 11, 11)
"table_name": "table_name_3"}
}
```

## Task 3. Run the DAGs

**Short task description:**

Run your DAG on Airflow Webserver locally and make sure there are no issues.

**Steps:**

1. Start airflow webserver with `$ airflow webserver` command
2. Start airflow scheduler with `$ airflow scheduler` command
3. Put your DAG file in dag_folder
4. Check Airflow UI
5. If you see any issues and tracebacks - fix them (but first read the next step)
6. You must see only one DAG on the UI dashboard. Not 3. And it will be the last DAG in your config dict.
Why is this? We will find this out in the next module.
7. After clicking on DAGs name you should see your DAG containing  three subsequent tasks `task_1 → task_2 → task_3`.
8. Run the DAG with either of the methods learned and check that it works correctly: all tasks must have a status ‘success’, and DAG should also be finished with ‘success’ status.

## Task 4. Refactor dynamic DAG creation and add Branching

**Steps:**
1. Refactor your code to dynamically create DAGs so that all three DAGs appeared in UI.
2. Then add a BranchOperator:
   
   What will happen if we want to insert a row in a table which doesn’t exist yet?  Of course, we’ll get an error! But how can we fix it?
   
   We need to check if the table exists and if an answer is ‘no’, we need to create it. So, we need BranchPythonOperator as a task that checks for the existence of our table. Right now we only work with dummy tasks, so the function we pass to Branchoperator as callable may just always return the same branch (“insert_row”). Example implementation:

3. Run the DAG and look at the DAG’s behavior.

## Task 5. Add correct Trigger Rule and more tasks

**Steps:**
1. Change the trigger rule to NONE_FAILED in your task that is the first common for both branches(insert row task).
2. After changing a trigger rule check a DAG behavior in UI (start dag and check correctness of work).
   
   Now we want to add one more task. Let’s check how you can run any command and execute any shell script you want - of course with bash and BashOperator. For our pipeline we will execute a simple command that will return the name of the system user airflow executor runs from. This can be done by running the “whoami” command.
3. Add this task with BashOperator as a second step in our pipeline

## Task 6. Create a new DAG
**Main Idea**

Our new DAG will trigger one of our generated table update DAGs. Our trigger DAG will wait for file ‘run’ in some folder to appear and then trigger the table updating DAG, wait for the triggered DAG to finish - and remove the ‘run’ file that it was waiting for.

**Steps:**
1. Create `trigger_dag.py` file.
2. Instantiate DAG and add three tasks into it:
   - **FileSensor** (use `from airflow.sensors.filesystem`). You can use any path you want for the trigger file.
   - **TriggerDagRunOperator**(use `from airflow.operators.trigger_dagrun import TriggerDagRunOperator`)
   - **BashOperator** (remove file with the rm command)
3. Put a new DAG file in `dag_folder`, refresh Airflow Web UI.
4. Run DAG
5. Put a trigger file into an expected path (file name and path, that you use in FileSensor) and verify Sensor has noticed the ‘run’ file  and external DAG was triggered.

## Task 7. Add SubDAG and Variables in trigger DAG
**Main Idea**

We will get a path to file for the Sensor to watch  from Variable. Before that it was simply hardcoded, now we will store it in Airflow Variables. But, we will also add a check - if a variable does not exist in Airflow Variables, use default from source code.

So, we need to do something like:
```
path = Variable.get('name_path_variable', default_var=’run’)
```

You can use any name to define a variable. There you will store a path ‘run’ file.

Also, we need to modify the last task and convert it to SubDag ‘process results’.

**Steps:**

1. Define SubDag with SubDagOperator

2. Inside SubDAG you will have four tasks:
   - Sensor to validate status of triggered DAG (must be success)
   - Print the result (PythonOperator)
   - Remove `run` file (BashOperator)
   - Create `finished_#timestamp` file (BashOperator)

   And you will get:

   **Main DAG-Trigger**

   ```
   Sensor: wait run file -> Trigger DAG -> Process results SubDAG
   ```

   **SubDAG**

   ```
   Sensor: triggered DAG -> Print result -> Remove run file -> Create `finished_#timestamp` file
   ```
   
   1. To create a sensor, use an ExternalTaskSensor [externaltasksensor](https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/external_task_sensor.html#externaltasksensor).

   2. To create `finished_#timestamp` file use BashOperator.

   For timestamp, use `{{ ts_nodash }}` from macros.

   So, your file name will have a suffix with dag execution date in iso format.

   3. for task `print a result (PythonOperator)` see point 3 below.

3. To create a task with `print a result (PythonOperator)` you need to use XCom.

   Open your table’s DAGs (`jobs_dag.py`) and add xcom_push() to the last task of the DAG.

   Message to push to Xcom is `{{ run_id }} ended”`

   1. Inside the  “print the result” task: get this Xcom with xcom_pull() and print the read value to the log.

   2. After first print statement (3.1) add statement to print whole task’s context dict (check what exists in execution context)

4. Save the DAGs, put in dags_folder and check that everything works fine.

If your Airflow setup is identical to one described in previous modules you’ll notice that the first task of automatically triggered DAG (message prin) has completed but no other task of this DAG is being run and the ExternalTaskSensor task keeps unsuccessfully checking the “child” DAG result and finally fails. The reason for this behavior is the executor type being used. Proceed to the next module to find out how to get this issue resolved.

## Task 8. Install and use PostgeSQL (Part I)

**Steps:**

1. Create Infrastructure. Choose a variant that is optimal for you - work with Docker or without and prepare infrastructure.

2. After you prepare all infrastructure and run Airflow.

3. Now’s the time to change our table DAG.

   3.1. Modify the 2nd task with `"getting current user"` command. Push the result of this command to Xcom.

   3.2 Define more meaningful names for tables in DAG config. Modify the `"check table exists"` task to do real check. We don’t have Postgres Operator to check table, so you need to define python callable using PostgresHook, take a look at an example:

   3.3 Now change the `"create table"` task. Use schema for tables.

   3.4 Change `insert_row` task to use `PostgresOperator` with query.

   3.5 Change query_table task to use `PythonOperator`. Define `python_callable` that uses `PostgreSQLHook` to get the number of rows in the table.

## Task 9. Install and use PostgreSQL (Part II)
**Steps:**
1. Let’s create our custom Operator - `PostgreSQLCountRows` (you can use any name that you want).
2. Modify your table DAGs. Import your `PostgreSQLCountRows` operator from the file you have created. Change task query_table to use `PostgreSQLCountRows` operator.
3. Run you DAG and test if everything works fine.

## Task 10. Slack Alerting
Add slack alerting for your slack workspace.

## Installation
You need to clone project to your computer:

```
git clone git@github.com:gridu/AIRFLOW-esamarkina.git
```

Project requires [pip3](https://pypi.org/project/pip/) and [python3](https://www.python.org/downloads/) installation.
Python 3.9.1 version is preferable. You can use [virtual env](https://docs.python.org/3/tutorial/venv.html)
instead of Python installed on your computer.
Steps for using virtual-env:
1. Create the virtual-env
   ```
   $ python3 -m venv <your-virtual-env-name>
   ```
2. Activate the virtual-env
   ```
   $ source <your-virtual-env-name>/bin/activate
   ```
3. After that you can install all the libraries necessary for the work
   ```
   $ pip3 install -r requirements.txt
   ```

### Airflow installation
[Airflow documentation](https://airflow.apache.org/docs/apache-airflow/stable/start/local.html)
1. Airflow needs a home, `~/airflow` is the default, but you can lay foundation somewhere else if you prefer
   ```
   $ export AIRFLOW_HOME=~/AIRFLOW-esamarkina
   ```

2. Initialize the database
   ```
   $ airflow db init
   ```
3. Create the user:

   ```
   $ airflow users create \
       --username admin \
       --firstname Peter \
       --lastname Parker \
       --role Admin \
       --email spiderman@superhero.org
   ```
   
   If you want to delete user from Airflow:
   ```
   $ airflow users delete -u <username>
   ```
4. Start the web server, default port is 8080
   ```
   $ airflow webserver --port 8080
   ```

5. Start the scheduler. 
   Open a new terminal or else run webserver with ``-D`` option to run it as a daemon
   ```
   $ airflow scheduler
   ```

## Run the project

1. Open your virtual env for this project:
   ```
   $ source myvenv/bin/activate
   ```

2. Export the environment variable AIRFLOW_HOME set to your Airflow’s home directory and start the web server, default port is 8080: 
    ```
   $ export AIRFLOW_HOME=~/Documents/Python/airflow-tasks
   $ airflow webserver --port 8080
   ```
   
3. Open a new terminal, activate the virtual environment and export the environment variable AIRFLOW_HOME set to your Airflow’s home directory, and run:
   ```
   $ export AIRFLOW_HOME=~/Documents/Python/airflow-tasks
   $ airflow scheduler
   ```
   (needed only if you haven’t started the scheduler previously)