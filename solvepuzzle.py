import sys
import time

class BK_PathResults:  #used for passing the results of backtrack
    def __init__(self, result, state, stateList, operations, costs):
        self.result = result
        self.stateTried = state
        self.pbStateList = stateList #passback stateList
        self.pbOperations = operations
        self.pbCosts = costs

class TS_PathResults: #used for passing the results of treesearch
    def __init__(self, result, path, ops, costs):
        self.result = result
        self.path = path
        self.ops = ops
        self.costs = costs

class Node:
    def __init__(self, data, IDnum, parent=None, depth=0, g=0, op=""):
        self.data = data
        self.ID = ("N" + str(IDnum))
        self.parent = parent
        self.children = set()
        self.depth = depth
        self.g = g
        self.h = estimateH(self.data.copy())
        self.calcF()
        self.op = op

    def replaceNodePosition(self, newParent, newOp): #node has a new parent
        self.parent.children.remove(self) #remove node from list of parent's children
        self.parent = newParent #set new parent
        self.op = newOp
        self.g = self.parent.g + int(self.op[0])-1 #updated the cost of getting to the node
        self.calcF()
        self.parent.children.add(self)
        self.depth = self.parent.depth+1
        
    def addChild(self, node):
        node.parent = self
        self.children.add(node)

    def isOwnAncestor(self): #check to see if this node has an ancestor identical to it
        curr = self
        while curr.parent != None: #iterate through parents
            curr = curr.parent
            if curr.data == self.data:
                return True
        return False

    def calcF(self): #calculates and sets f
        self.f = self.g + self.h

class Tree:
    def __init__(self, rootNode):
        self.root = rootNode #the starting node in the tree. The rest of the tree can be reached from here.
        assert self.root.parent is None, "Root node cannot have a parent" #root node cannot have a parent
        self.nodes = {}
        self.addNode(self.root)

    def findPath(self, startingNode, targetNode): #iterate through parents from target node back to starting node
        path = [targetNode]
        curr = targetNode.parent
        while curr != startingNode: #starts from targetNode and goes up the tree until startingNode is reached
            path.append(curr)
            curr = curr.parent
        path.append(startingNode)
        path.reverse() #list to be resturned in top->bottom order
        return path

    def addNode(self, newNode):
        self.nodes["".join(newNode.data)] = newNode #add to hashmap of nodes. The key is a string of the state of the node.

    def containsData(self, data): #check if node in tree
        return ("".join(data) in self.nodes.keys())
    
    def findPathOps(self, path): #returns all the operators in the path
        ops = []
        for node in path:
            ops.append(node.op)
        return ops
    
    def findPathCost(self, path): #returns all the costs (at each stage) in the path
        costs = []
        for node in path:
            costs.append(node.g)
        return costs

def isSolution(state): #check if the given state meets the solition criteria
    lowestBlack = state.index('B')
    return state[lowestBlack:].count('W') == 0 #no Ws after first B

def isDeadEnd(state): #check if state is invalid
    return not (state.count('B') >= 1 and state.count('W') >= 1 and state.count('E') == 1 and len(state) == 7)

def move(operator, state): #perform the given operation on the given state and return the new state
    operator = list(operator)
    distance = int(operator[0]) #this should always be the move distance
    if 'L' in operator:
        distance = 0-distance #if moving left, distance should be negative
    idx = state.index('E')
    state[idx], state[idx+distance] = state[idx+distance], state[idx] #swap
    return state

def estimateH(state): #get the heuristic evaluation of state
    if isSolution(state):
        return -0.5
    
    state = list(state)
    eState = state.copy() #keep a copy of state that contains E
    state.remove('E') 
    h = hDistanceFromSolution(state) #finding wCost doesn't require E being in the state
    h = hEOptimality(h, eState) 
    return h

def hDistanceFromSolution(state): #Calculate the state's 'distance' from the solution
    firstB = state.index('B')
    rightWBeforeB = firstB-1 #right-most W before the first B
    leftWAfterB = state[firstB:].index('W') + firstB #left-most W after the first B
    bCount = state.count('B')
    h = 0
    counts = []
    for i in range(firstB, len(state)): #each W that isn't before the first B will add to the state's distance from solution
        if state[i] == 'W':
            counts.append(state[firstB:i].count('B')) #amount of Bs the current W will need to hop over to reach a position that could satisfy the success criteria
            assert counts[-1] >= 0, "Invalid state" #Precondition check
    h = sum(counts)
    return h

def hEOptimality(h, eState): #Calculate the optimality of the state's position of 'E' (refines our ordering decision)
    ePos = eState.index('E')
    eFirstB = eState.index('B')
    eRightWBeforeB = -1
    for i in range(len(eState[:eFirstB])):
        if eState[i] == 'W':
            eRightWBeforeB = i #index of rightmost W that is before the leftmost B
    eLeftWAfterB = eState[eFirstB:].index('W') + eFirstB
    eOpt = max(eRightWBeforeB+1, eLeftWAfterB-2) #optimal position of E
    diff = abs(eOpt - ePos) #distance of current E position to optimal E position

    if diff == 0:
        diff = 0.9
    h -= (1/diff) #slightly reduce h based on the optimality of E's position
    return h

def getOperators(state): #returns a list of valid operators for the given state 
    ops = []
    left = state.index('E')
    right = min(3, 6-left)
    left = min(3, left)

    leftOps =[]
    rightOps = []
    
    for i in range(left):
        leftOps.append(str(i+1)+"L") #generate valid L operators
        
    for i in range(right): 
        rightOps.append(str(i+1)+"R") #generate valid R operators

    priority = 1 #sort operators in order of preference for backtrack
    for i in range(3):
        if len(leftOps) >= priority:
            ops.append(leftOps[priority-1])
        if len(rightOps) >= priority:
            ops.append(rightOps[priority-1])
        if priority == 1:
            priority = 3
        else:
            priority = 2  
    return ops

def sortDLS(openList): #sort the openList for depth-limited search
    for i in range(1, len(openList)): #sort open by depth in descending order
        j = i
        while (j > 0) and (openList[j-1].depth < openList[j].depth):
            openList[j], openList[j-1] = openList[j-1], openList[j]
            j -= 1
    return openList #because the states generated by getOperators() were in priority order, the above algorithm will keep that order after sorting by depth

def sortA(openList): #sort the openList for Algorithm A
    for i in range(1, len(openList)): #sort openList by f in ascending order
        j = i
        while (j > 0) and ((openList[j-1].f) > (openList[j].f)):
            openList[j], openList[j-1] = openList[j-1], openList[j]
            j -= 1
            
    return openList

def treeSearch(state, flag, algorithm):
    s = Node(state, 0)
    count = 0
    tree = Tree(s)
    openList = [s] #contains Node objects
    closedList = []
    depth = 0
    maxDepth = 55 #maximum depth allowed for DLS
    n = s #redundancy for if the loop is never entered
    
    while(len(openList)>0): #while openList is not empty
        n = openList[0] #current node
        openList = openList[1:] #remove current node from openList
        closedList.append(n) #add current node to closedList
        
        if isSolution(n.data): #return all relevant data for output
            path = tree.findPath(s, n)
            ops = tree.findPathOps(path)
            costs = tree.findPathCost(path)
            return TS_PathResults(True, path, ops, costs)
        
        ops = getOperators(n.data)
        ops.reverse() #DLS requires operators to be in reverse order of BK's priority
        
        m = set() #set of nodes generated but not yet in tree

        if flag > count: #do this [flag] times
            openPrint = [] #collect node data for openList
            for node in openList:
                openPrint.append("".join(node.data))
                
            closedPrint = [] #collect node data for closedList
            for node in closedList:
                closedPrint.append("".join(node.data))
                
            print("Expansion:\tNode ID: %s\n\t\tExpansion order: %s\n\t\tg: %f, h: %f, f: %f\n\t\tOPEN: %s\n\t\tCLOSED: %s\n" %(n.ID, ", ".join(ops), n.g, n.h, n.f, ", ".join(openPrint), ", ".join(closedPrint))) #print node details
        
        for i in ops:
            count += 1
            child = Node(move(i, n.data.copy()), count, n, n.depth+1, n.g+int(i[0])-1,i) #generate new node
            if algorithm == "DLS":
                if child.depth > maxDepth:
                    child.parent = child #force child to fail upcoming ancestor check
            
            if not child.isOwnAncestor():
                if flag >= count:
                    print("Generation:\tOperator applied: %s\n\t\tNode ID: %s\n\t\tNode's parent: %s\n\t\tg: %f, h: %f, f: %f\n" %(i, child.ID, n.ID, child.g, child.h, child.f)) #for each node generated, print node details
                m.add(child)

        for i in m:
            if not tree.containsData(i.data):
                n.addChild(i) 
                tree.addNode(i) #add items in m to tree
                openList.append(i)
            else:
                if algorithm == "A":
                    if tree.nodes["".join(i.data)].f > i.f: #if new version of node more efficient, replace old version
                        tree.nodes["".join(i.data)].replaceNodePosition(i.parent, i.op)

        if algorithm == "DLS": #sort openList appropriately
            openList = sortDLS(openList)
        else:
            openList = sortA(openList)

        
    path = tree.findPath(s, n) #path taken
    ops = tree.findPathOps(path) #operators used
    costs = tree.findPathCost(path) #cost of getting to each node on path
    return TS_PathResults(False, path, ops, costs)

def BK(stateList, flag, count, opsUsed, cost): 
    bound = 132 

    state = stateList[-1]
    for node in stateList[:-1]: 
        if node.data == state.data: #if node already in stateList
            if flag >= count:
                print("Backtracking: ANCESTOR\n")
            return BK_PathResults(False, state, stateList, opsUsed, cost), count #true is success, false is fail
    
    if isSolution(state.data):
        return BK_PathResults(True, state, stateList, opsUsed, cost), count

    if isDeadEnd(state.data):
        print("Backtracking: DEADEND") #this should never happen as the getOperators function only returns valid operators
        return BK_PathResults(False, state, stateList, opsUsed, cost), count

    

    if count > bound: #check if bound has been reached
        if flag >= count:
            print("Backtracking: BOUND REACHED\n")
        return BK_PathResults(False, state, stateList, opsUsed, cost), count

    operators = getOperators(state.data)
    pathResults = BK_PathResults(False, None, None, None, 0) #create dummy obj for initial loop check
    while not pathResults.result: #while new paths are bad, try other paths until out of ops
        if len(operators)==0:
            if flag >= count:
                print("Backtracking: NO MORE OPS\n")
            return BK_PathResults(False, state, stateList, opsUsed, cost), count
        op = operators.pop() #take highest priority operator and removeit from list
        count += 1
        newState = Node(move(op, state.data.copy()), count)
        if flag >= count: #Do this on the first [flag] node generations
            operatorsPrint = ", ".join(operators)
            opsUsedPrint = ", ".join(opsUsed)
            print("Flag:\tOperator: %s\n\tGenerated Node ID: %s\n\tAvailable operators: %s\n\tSuccessful operations used so far: %s\n" %(op, newState.ID, operatorsPrint, opsUsedPrint))
        
        opsUsed.append(op) 
        if len(cost) > 0: #update cost value
            cost.append(cost[-1] + (int(op[0])-1))
        else:
            cost.append((int(op[0])-1))

        
        stateList.append(newState) 
        pathResults, count = BK(stateList, flag, count, opsUsed, cost)
        if not pathResults.result:
            if count > bound:
                operators = [] 
            else:
                del stateList[-1]
                del opsUsed[-1]
                del cost[-1]
    return pathResults, count


if __name__ == "__main__":
    #possible entry: solvepuzzle.py BBBWWWE BK result1 0

    assert len(sys.argv) == 5, "Please enter three arguments"
    puzzleString = sys.argv[1]
    procedureName = sys.argv[2]
    outputFileName = sys.argv[3]
    flag = sys.argv[4]

    #verify puzzleString validity
    assert type(puzzleString) is str, "Puzzle format must be string"
    puzzleString = puzzleString.upper()
    assert puzzleString.count('B') >= 1 and puzzleString.count('W') >= 1 and puzzleString.count('E') == 1 and len(puzzleString) == 7, "Puzzle string must be a 7 character string containing at least one of both B and W, and exactly one E."
    puzzleList = list(puzzleString)


    #verify procedureName validity
    assert type(procedureName) is str, "Procedure type must be string"
    procedureName = procedureName.upper()
    valid = ['A', 'BK', 'DLS']
    assert procedureName in valid, "Procedure type must be 'A', 'BK' or 'DLS'"
    
    #outputFileName does not need verifying

    #verify flag validity
    if flag.isdigit():
        flag = int(flag)
    else:
        assert type(flag) is int and flag>=0, "Flag must be a non-negative integer"


    print(procedureName + "\n")
    if procedureName == 'BK':
        result, count = BK([Node(puzzleList, 0)], flag, 0, [], [])
        f = open(outputFileName, "w")
        toWrite = [("start  " + "".join(result.pbStateList[0].data) + "  0")] #first line to write to file
        
        for i in range(len(result.pbOperations)):
            toWrite.append(result.pbOperations[i] + "  " + "".join(result.pbStateList[i+1].data) + "  " + str(result.pbCosts[i])) #generate list of lines to be written to file
        if result.result:
            print("Success.")
        else:
            print("Failed: Bound too small.")
        f.write("\n".join(toWrite))
        f.close()
        
    else:
        result = treeSearch(puzzleList, flag, procedureName)
        f = open(outputFileName, "w")
        toWrite = []
        toWrite.append("start  " + "".join(result.path[0].data) + "  " + str(result.costs[0])) #first line to write to file
        for i in range(1, len(result.path)):
            toWrite.append(result.ops[i] + "  " + "".join(result.path[i].data) + "  " + str(result.costs[i])) #generate list of lines to be written to file
        if result.result:
            print("Success.")
        else:
            print("Failed: Depth too limited.") #A should not be able to fail unless it crashes for some reason
        f.write("\n".join(toWrite))
        f.close()
    
    
