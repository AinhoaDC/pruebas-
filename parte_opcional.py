#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  9 19:57:42 2023

@author: Ainhoa
"""
from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Array

from time import sleep
from random import random, randint

N = 10
K = 4
NPROD = 3
NCONS = 1

def delay(factor = 3):
    sleep(random()/factor)

#Con la siguiente función añadimos el elemento producido por un productor a storage.
def add_data(storage,pid, data, mutex, productores):
    mutex.acquire()
    try:
        #Tenemos que tener en cuenta a la hora de añadir elementos que en la posición en la que vamos a añadir 
        #sea un -2 y además no se salga del búfer del productor. 
        for j in range(K*pid ,K*pid+K): 
            if storage[j] == -2: 
                storage[j] = data 
                break 
        productores[pid] = pid 
        delay(6)
    finally:
        mutex.release() 

#La función a continuación sirve para añadir un -1 cuando un productor ha terminado de producir. 
def add_data1(storage,pid, data, mutex,productores): 
    mutex.acquire()
    try: 
        #Se añade un -1 al final del búfer, en el primer elemento que sea -2, porque aunque el productor 
        #deje de producir puede ser que tenga varios elementos ya producidos que haya consumir, por ello, 
        #no podemos añadir el -1 en cualquier lugar, si no al final. 
        for j in range(K*pid ,K*pid+K): 
            if storage[j] == -2: 
                storage[j] = -1
                break 
        productores[pid] = pid 
        delay(6)

    finally: 
        mutex.release()


def producer(storage,empty, non_empty, mutex, productores):
        data = 0
        for v in range(N): 
            print (f"producer {current_process().name} produciendo")
            delay(6)
            data += randint(1,6)
            empty.acquire()
            add_data(storage,int(current_process().name.split('_')[1]),
                     data, mutex, productores)
            non_empty.release()
            print (f"producer {current_process().name} almacenado {v}")
        empty.acquire()
        add_data1(storage, int(current_process().name.split('_')[1]),v, mutex, productores) 
        non_empty.release()



def consumer(storage,empty, non_empty, mutex, lista_cons, productores): 
    i = 0
    for i in range(NPROD): 
        non_empty[i].acquire() 
    while  i < NPROD:
        i = 0
        #El siguiente bucle es para comprobar cuando el primer elemento de cada bufer de cada productor es -1, 
        #eso es lo que nos indicará cuando el proceso ha terminado. 
        for p in range(NPROD): 
            if storage[p*K] == -1 : 
                i+=1
        if i == NPROD: 
            break 
        minimo = 1000
        pos = 0 
        #No podemos usar la función mínimo para hallarlo puesto que si hay un -1 ese será el número que cogerá
        #por tanto lo hacemos comprobando el primer elemento de cada bufer de cada productor, y comparándolos. 
        for j in range(0,len(storage),K): #El range va de 0 a la longitud del storage con salto K (la longitud del búfer).
            if minimo > storage[j] and storage[j] >= 0 : 
                minimo = storage[j] 
                pos = j  
        productor = productores[pos//K] 
        #Cuando consumimos un elemento, se queda vacío y se pone -2. En este caso, tenemos que mover todos los elementos 
        #una posición hacia delante y poner el -2 al final del búfer del productor. 
        for l in range(pos,pos+K): 
            if l != pos+K-1: 
                storage[l] = storage[l+1]  
            else: 
                storage[l] = -2 
        empty[productor].release() 
        delay()  
        non_empty[productor].acquire() 
        #Creamos una lista creciente donde almacenamos el productor que ha producido el valor minimo, y dicho valor. 
        lista_cons.append((productor, minimo)) 
        print(lista_cons)
        
def main():
    storage = Array('i',K*NPROD) #Creamos el storage de K (longitud del bufer) * NPROD (número de productores).
    lista_cons = [] 
    productores = Array('i',NPROD)
    for i in range(K*NPROD):
        storage[i] = -2
    print ("almacen inicial", storage[:])
    #Creamos una lista de semáforos, porque ahora lo que queremos es poder usar varios semáforos.
    non_empty = []
    empty = []
    mutex = Lock()
    for i in range(N):
        non_empty.append(Semaphore(0))
        empty.append(BoundedSemaphore(K)) #En este caso el BoundedSemaphore tiene que ser de tamaño K, para poder tener un búfer de tamaño K. 
     
    prodlst = [ Process(target=producer,
                        name=f'prod_{i}',
                        args=(storage,empty[i], non_empty[i], mutex, productores))
                for i in range(NPROD) ]

    conslst = [ Process(target=consumer,
                      name=f"cons_{i}",
                      args=(storage, empty, non_empty, mutex,lista_cons,productores))
                for i in range(NCONS) ]

    for p in prodlst + conslst:
        p.start()

    for p in prodlst + conslst:
        p.join()


if __name__ == '__main__':
    main()

