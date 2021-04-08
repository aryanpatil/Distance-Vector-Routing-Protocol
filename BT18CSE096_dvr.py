import sys
from threading import Thread, Lock
from queue import Queue
import time
import copy

mutex = Lock()

# Create a global graph and queue for communication among threads
global g_graph
global Q

# Initial graph creating function
def create_global_graph(names, num_routers):
    
    graph = {}

    for i in range(num_routers):
        graph[names[i]] = {}

    return graph

# Creating global queue function
def create_global_queue(names, num_routers):
    q = {}

    for i in range(num_routers):
        q[names[i]] = Queue()

    return q

# Create routing table class
class Routing_table:

    # Constructor
    def __init__(self, name ):
        self.name = name                    # Router name
        self.dv = {}                        # Router Table
        self.modified = {}                  # Modified Values
        for dest in g_graph.keys():         # Initialization
            if dest!=name:
                self.dv[dest] = -1
                self.modified[dest] = ""

        for dest in g_graph[name].keys():   # Extracting initial values from global graph
            self.dv[dest] = g_graph[name][dest]


    # Display function
    def display_table(self):
        print("---------------------------------------------------")
        print("Name of Router : ", self.name)
        print("---------------------------------------------------")
        print("{:<15} {:<15} {:<10}".format('Destination','Cost','Modified'))
        print("---------------------------------------------------")
        for dest in self.dv.keys():
            print("{:<15} {:<15} {:<10}".format(dest, self.dv[dest], self.modified[dest]))
        print("-------------------------------------------------------------------------------------------")



# Router functions
def router(name):
    
    r_table = Routing_table(name)           # Create routing table
    
    mutex.acquire()
    r_table.display_table()                 # Display initial table
    mutex.release()

    neighbours = len(g_graph[name].keys())  # Number of immediate neighbours

    for i in range(4):

        time.sleep(2)                       # Sleep for 2 seconds

        for dest in g_graph.keys():
            if dest!=name:                  # Unclear previous asterisks (*)
                r_table.modified[dest] = '' 

        mutex.acquire()
        for dest in g_graph[name].keys():   # Send tables to neighbouring routers
            Q[dest].put(copy.deepcopy(r_table))
        mutex.release()
        
        wait = 1

        while wait:                         # Wait until all nearby routers send their tables 
            if Q[name].qsize()==neighbours:
                wait = 0

        rts = []
        old_table = copy.deepcopy(r_table)

        while not Q[name].empty():          # Extract the queue
            rts.append(Q[name].get())

        for dest in r_table.dv.keys():      # Bellman Ford Algorithm
            if(old_table.dv[dest] != -1):
                min_cost = old_table.dv[dest]
            else:
                min_cost = 9999999

            for table in rts:
                if table.name!=dest:
                    if(table.dv[dest] != -1):
                        if(old_table.dv[table.name] + table.dv[dest] < min_cost):
                            min_cost = old_table.dv[table.name] + table.dv[dest]
                            r_table.modified[dest] = '*'                        # Mark as modified value

            if(min_cost != 9999999):
                r_table.dv[dest] = min_cost        

        mutex.acquire()  
        print("-------------------------------------------------------------------------------------------")  
        print("Iteration Number: ", (i+1),  " for Router Name: ", name)       
        r_table.display_table()
        mutex.release()


# Main function

# Catch the data file name from terminal
try:
    input_file = sys.argv[1]
except:
    print("Please specify valid file name!")

# Open the file and read the data
f = open(input_file, 'r')
num_routers = int(f.readline())         # Number of routers
names = f.readline().split()            # Names of routers

# Creating global graph
g_graph = create_global_graph(names, num_routers)

# Creating global Queue
Q = create_global_queue(names, num_routers)

while True:
    text = f.readline()
    if text=='EOF':                     # Exit loop if EOF 
        break
    else:
        cost = text.split()             # Split the sentence ['A', 'B', 'Cost']
        g_graph[cost[0]][cost[1]] = int(cost[2])
        g_graph[cost[1]][cost[0]] = int(cost[2])
        print(cost)
f.close()


# Creating Routers as threads
threads = []

for i in range(num_routers):
    t = Thread(target=router, args=(names[i],))
    t.start()
    threads.append(t)

# Wait for all the threads to join

for t in threads:
    t.join()
