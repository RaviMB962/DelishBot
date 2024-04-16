import mysql.connector

cnx = mysql.connector.connect(
    host = 'localhost', # Enter Host Type
    user = 'root', #Enter_UserName
    password = '*Ra900875', #Enter Password
    database= "pandeyji_eatery"# Enter Database Name
)


def insert_order_item(food_item, quantity, order_id):
    try:
        cursor = cnx.cursor()

        # calling the stored procedure
        cursor.callproc('insert_order_item',(food_item, quantity, order_id) )

        # committing changes
        cnx.commit()

        # close the cursor
        cursor.close()

        print("Order Item inserted successfully")

        return 1
    except mysql.connector.Error as err:
        print(f"Error in inserting order item: {err}")

        # Rollback Changes if necessary
        cnx.rollback()

        return -1
    
    except Exception as e:
        print(f"An error occured : {e}")

        #Rollback changes if necessary
        cnx.rollback()

        return -1


def get_next_order_id():

    cursor = cnx.cursor()

    # write the sql query
    query  = ("SELECT MAX(order_id) FROM orders")

    #Execute the query
    cursor.execute(query)

    #Fetch the result
    result = cursor.fetchone()[0]

    # close the cursor
    cursor.close()

    # Returning the available order_id 
    if result is None:
        return 1
    else:
        return result+1

def insert_order_tracking(order_id, status):
    cursor = cnx.cursor()

    #Inserting the record into the order_tracking table
    insert_query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"

    cursor.execute(insert_query, (order_id,status))

    # committing the changes
    cnx.commit()

    # closing the cursor
    cursor.close()

def get_total_order_price(order_id):
    cursor = cnx.cursor()

    # write the sql query
    query  = f"SELECT get_total_order_price({order_id})"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()[0]

    # closing the cursor
    cursor.close()

    return result


def get_order_status(order_id: int):
    #create cursor object
    cursor = cnx.cursor()

    # write the sql query
    query  = ("SELECT status FROM order_tracking WHERE order_id = %s")

    #Execute the query
    cursor.execute(query, (order_id,))

    #Fetch the result
    result = cursor.fetchone()

    # close the cursor
    cursor.close()

    if result is not None:
        return result[0]
    else:
        return  None