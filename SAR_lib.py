import json
from nltk.stem.snowball import SnowballStemmer
import os
import re
import math

class SAR_Project:
    """
    Prototipo de la clase para realizar la indexacion y la recuperacion de noticias

        Preparada para todas las ampliaciones:
          parentesis + multiples indices + posicionales + stemming + permuterm + ranking de resultado

    Se deben completar los metodos que se indica.
    Se pueden añadir nuevas variables y nuevos metodos
    Los metodos que se añadan se deberan documentar en el codigo y explicar en la memoria
    """

    # lista de campos, el booleano indica si se debe tokenizar el campo
    # NECESARIO PARA LA AMPLIACION MULTIFIELD
    fields = [("title", True), ("date", False),
              ("keywords", True), ("article", True),
              ("summary", True)]


    # numero maximo de documento a mostrar cuando self.show_all es False
    SHOW_MAX = 10


    def __init__(self):
        """
        Constructor de la classe SAR_Indexer.
        NECESARIO PARA LA VERSION MINIMA

        Incluye todas las variables necesaria para todas las ampliaciones.
        Puedes añadir más variables si las necesitas

        """
        self.term_field = {}
        self.weight_doc = {}
        self.index = {} # hash para el indice invertido de terminos --> clave: termino, valor: posting list.
                        # Si se hace la implementacion multifield, se pude hacer un segundo nivel de hashing de tal forma que:
                        # self.index['title'] seria el indice invertido del campo 'title'.
        self.posindex = {}
        self.sindex = {} # hash para el indice invertido de stems --> clave: stem, valor: lista con los terminos que tienen ese stem
        self.ptindex = {} # hash para el indice permuterm.
        self.docs = {} # diccionario de documentos --> clave: entero(docid),  valor: ruta del fichero.
        self.weight = {} # hash de terminos para el pesado, ranking de resultados. puede no utilizarse
        self.news = {} # hash de noticias --> clave entero (newid), valor: la info necesaria para diferenciar la noticia dentro de su fichero (doc_id y posición dentro del documento)
        self.tokenizer = re.compile("\W+") # expresion regular para hacer la tokenizacion
        self.stemmer = SnowballStemmer('spanish') # stemmer en castellano
        self.show_all = False # valor por defecto, se cambia con self.set_showall()
        self.show_snippet = False # valor por defecto, se cambia con self.set_snippet()
        self.use_stemming = False # valor por defecto, se cambia con self.set_stemming()
        self.use_ranking = False  # valor por defecto, se cambia con self.set_ranking()
        self.pterms = {} # hash para el indice invertido permuterm --> clave: permuterm, valor: lista con los terminos que tienen ese permuterm


    ###############################
    ###                         ###
    ###      CONFIGURACION      ###
    ###                         ###
    ###############################


    def set_showall(self, v):
        """

        Cambia el modo de mostrar los resultados.

        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_all es True se mostraran todos los resultados el lugar de un maximo de self.SHOW_MAX, no aplicable a la opcion -C

        """
        self.show_all = v


    def set_snippet(self, v):
        """

        Cambia el modo de mostrar snippet.

        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_snippet es True se mostrara un snippet de cada noticia, no aplicable a la opcion -C

        """
        self.show_snippet = v


    def set_stemming(self, v):
        """

        Cambia el modo de stemming por defecto.

        input: "v" booleano.

        UTIL PARA LA VERSION CON STEMMING

        si self.use_stemming es True las consultas se resolveran aplicando stemming por defecto.

        """
        self.use_stemming = v


    def set_ranking(self, v):
        """

        Cambia el modo de ranking por defecto.

        input: "v" booleano.

        UTIL PARA LA VERSION CON RANKING DE NOTICIAS

        si self.use_ranking es True las consultas se mostraran ordenadas, no aplicable a la opcion -C

        """
        self.use_ranking = v




    ###############################
    ###                         ###
    ###   PARTE 1: INDEXACION   ###
    ###                         ###
    ###############################


    def index_dir(self, root, **args):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Recorre recursivamente el directorio "root" e indexa su contenido
        los argumentos adicionales "**args" solo son necesarios para las funcionalidades ampliadas

        """
        self.multifield = args['multifield']
        self.positional = args['positional']
        self.stemming = args['stem']
        self.permuterm = args['permuterm']


        for dir, subdirs, files in os.walk(root):
            for filename in files:
                if filename.endswith('.json'):
                    fullname = os.path.join(dir, filename)
                    self.index_file(fullname)

        if self.stemming:
            self.set_stemming(True)
            self.make_stemming()
        if self.permuterm:
            self.make_permuterm()

        ##########################################
        ## COMPLETAR PARA FUNCIONALIDADES EXTRA ##
        ##########################################

        

    def index_file(self, filename):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Indexa el contenido de un fichero.

        Para tokenizar la noticia se debe llamar a "self.tokenize"

        Dependiendo del valor de "self.multi field" y "self.positional" se debe ampliar el indexado.
        En estos casos, se recomienda crear nuevos metodos para hacer mas sencilla la implementacion

        input: "filename" es el nombre de un fichero en formato JSON Arrays (https://www.w3schools.com/js/js_json_arrays.asp).
                Una vez parseado con json.load tendremos una lista de diccionarios, cada diccionario se corresponde a una noticia

        """

        with open(filename) as fh:
            
            i = 0 #Contador para los articulos dentro del fichero
            #fname = filename.split("\\")[2][:-5] #Split para sacar el nombre base
     
            jlist = json.load(fh)
            d = len(self.docs) #DocId
            self.docs[d] = filename

            if self.positional:
                for new in jlist:
                    n = len(self.news) #NewId

                    self.news[n] = f"{d}_{i}" #Asignar al newId su nombre junto con la posición relativa
      
                    words = self.tokenize(new["article"])
                    j = 0
                    for w in words:
                        if w in self.index.keys():
                            if n not in self.index[w]:
                                self.index[w].append(n)
                        if w in self.posindex.keys():
                            if n not in self.posindex[w].keys():
                                self.posindex[w][n] = [j]
                            else:
                                self.posindex[w][n].append(j)
                        else:
                            self.index[w] = [n]
                            self.posindex[w] = {n : [j]}
                        j = j + 1
                    i = i + 1
            else:
                for new in jlist:
                    
                    n = len(self.news) #NewId
                    self.news[n] = f"{d}_{i}" #Asignar al newId su nombre junto con la posición relativa
                    words = self.tokenize(new["article"])
                    j = 0
                    for w in words:
                        if w in self.index.keys():
                            if n not in self.index[w]:
                                self.index[w].append(n)
                                self.posindex[w]
                        else:
                            self.index[w] = [n]
                            self.posindex[w] = {n : [j]}
                        j = j + 1
                    i = i + 1
            fh.close()




    def tokenize(self, text):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Tokeniza la cadena "texto" eliminando simbolos no alfanumericos y dividientola por espacios.
        Puedes utilizar la expresion regular 'self.tokenizer'.

        params: 'text': texto a tokenizar

        return: lista de tokens

        """
        return self.tokenizer.sub(' ', text.lower()).split()



    def make_stemming(self):
        """
        NECESARIO PARA LA AMPLIACION DE STEMMING.

        Crea el indice de stemming (self.sindex) para los terminos de todos los indices.

        self.stemmer.stem(token) devuelve el stem del token

        """
         # Recorremos todos los campos del índice de términos

        for word in self.index.keys():

            # Recorremos todos los términos del campo
                # Generamos el stem solo si no hemos hecho el stemming del término con anterioridad
            stem = self.stemmer.stem(word)

            if stem in self.sindex.keys():
                if word not in self.sindex[stem]:
                    self.sindex[stem].append(word)
            else:
                self.sindex[stem] = [word]
            # Añadimos el stem si no lo hemos añadido todavía
            #self.sindex[stem] = self.or_posting(self.sindex[field].get(stem, []),self.index[field][term])



    def make_permuterm(self):
        """
        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        Crea el indice permuterm (self.ptindex) para los terminos de todos los indices.

        """

        ####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE STEMMING ##
        ####################################################
     # Recorremos todos los campos del índice de términos
        for term in self.index.keys():
            aux = term + "$"
            i=0
            if aux not in self.ptindex.keys():
                for w in aux:
                    pterm = aux[i:] + aux[0:i]
                    self.ptindex[pterm] = term
                    i=i+1



    def show_stats(self):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Muestra estadisticas de los indices

        """

        print('========================================')
        print('Número de días indexados: {}'.format(len(self.docs)))
        print('----------------------------------------')
        print('Número de noticias indexadas: {}'.format(len(self.news)))
        print('----------------------------------------')
        print('TOKENS:')
        print("\t# tokens en 'index': {}".format(len(self.index.keys())))
        print('----------------------------------------')
        if (self.permuterm):
            print('PERMUTERMS:')
            print(f"\t# tokens en 'ptindex': {len(self.ptindex.keys())}")
            print('----------------------------------------')
        if (self.stemming):
            print('STEMS:')
            print(f"\t# tokens en 'sindex': {len(self.sindex.keys())}")
            print('----------------------------------------')
        if (self.positional):
            print('POSITIONALS:')
            print(f"Se permiten consultas posicionales")
        print('========================================')

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################


    ###################################
    ###                             ###
    ###   PARTE 2.1: RECUPERACION   ###
    ###                             ###
    ###################################


    def solve_query(self, query, prev={}):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una query.
        Debe realizar el parsing de consulta que sera mas o menos complicado en funcion de la ampliacion que se implementen


        param:  "query": cadena con la query
                "prev": incluido por si se quiere hacer una version recursiva. No es necesario utilizarlo.


        return: posting list con el resultado de la query

        """

        #normalizamos la query
        query = query.lower()

        #separamos los parentesis
        split = ""
        open = False
        for i in range(0,len(query)):
            item=query[i]
            if item == '(' or item == ')':
                split = split + " " + item + " "
            else:
                if item == '"':
                    open = not open
                if item == " " and open:
                    split = split + "|"
                else: split = split + item

        #separamos los diferentes items de la query
        query = split.split()

        #insertamos para que el primer término haga un OR con una lista vacía (así no hay problemas)
        query.insert(0,'or')

        #devolvemos el resultado llamando a un nuevo método que resuelva la query de forma recursiva
        return self.solve_query2(query,[])

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################

    def solve_query2(self,query,prev):
        """
        Resuelve una query de forma recursiva.

        param:  "query": cadena con la query
                "prev": parámetro recursivo que almacenará la posting list t1 en (t1 AND/OR t2)

        return: la posting list con el resultado de la query

        """

        new_query = ""      #query a procesar
        i=1                 #indica a partir de donde comienza new_query
        field = 'article'   #campo sobre el que se efectua la query

        if query is None or len(query) == 0:
            return prev
        else:
            #posting list para hacer "t1 AND/OR t2"
            t1 = prev

            #Analizamos el que va después del AND/OR por si hay que negar el siguiente término
            if query[1] != 'not' and query[1] != '(':
                term = query[1]
                field,term = self.colonSplit(term)

                t2 = self.get_posting(term, field)
                i=2

            elif query[1] != '(': #después del AND/OR hay un 'NOT'
                term = query[2] #item después del 'NOT'

                if term == '(': #tenemos que negar una consulta entre paréntesis
                    #resolvemos la consulta entre paréntesis
                    new_query = self.subconsulta(query[2:len(query)])
                    new_query.insert(0,'or')
                    t2_sin_negar = self.solve_query2(new_query,{})

                    #negamos la consulta
                    t2 = self.reverse_posting(t2_sin_negar)

                    #longitud de la subquery + 2 paréntesis + 'NOT' + 1 (contado en la subquery por 'OR')
                    i = len(new_query)+3
                else: #negamos solo un término
                    field,term = self.colonSplit(term)

                    t2 = self.reverse_posting(self.get_posting(term, field))
                    i=3
            else: #es un '('
                #obtenemos la consulta entre paréntesis
                new_query = self.subconsulta(query[1:len(query)])
                new_query.insert(0,'or')
                t2 = self.solve_query2(new_query,{})

                #longitud de la subquery + paréntesis + 1 (contado por 'OR' en len(new_query))
                i = len(new_query)+2

            #Actualizamos la lista según operador
            if query[0] == 'and':
                prev = self.and_posting(t1,t2)
            elif query[0] == 'or':
                prev = self.or_posting(t1,t2)

        #Actualizamos la posición desde donde empezará la siguiente parte
        new_query = query[i:len(query)]

        #devolvemos recursivamente
        return self.solve_query2(new_query,prev)

    def colonSplit(self,term):
        """
        Calcula el nuevo campo y recalcula el nuevo término

        param:  "term": término a consultar

        return: una tupla (field,term) con el campo y término correspondientes

        """

        field = 'article'
        colonSplit = term.split(':')
        if len(colonSplit) == 2:
            field = colonSplit[0]
            term = colonSplit[1]

        return field,term

    def subconsulta(self,query):
        """
        Obtiene la subconsulta entre paréntesis

        param:  "query": la consulta sobre la que realizar la subconsulta

        return: la subconsulta entre los paréntesis exteriores

        """

        j = 0 #contador de subconsultas

        #calcular donde acaba la subconsulta
        for i in range (0,len(query)):
            if query[i] == '(': j = j+1 #se abre subconsulta
            if query[i] == ')': j = j-1 #se cierra subconsulta
            if(j==0): break #se ha cerrado el primer paréntesis

        return query[1:i]

    def get_posting(self, term, field='article'):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Devuelve la posting list asociada a un termino.
        Dependiendo de las ampliaciones implementadas "get_posting" puede llamar a:
            - self.get_positionals: para la ampliacion de posicionales
            - self.get_permuterm: para la ampliacion de permuterms
            - self.get_stemming: para la amplaicion de stemming


        param:  "term": termino del que se debe recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """

        termAux = term

        #Se añade el término y campo de la consulta para el ranking
        self.term_field[(termAux, field)] = True

        res = []

        #Comprobamos si se debe realizar permuterms
        if ("*" in termAux or "?" in termAux):
            res = self.get_permuterm(termAux,field)

        if termAux[0] == '"' and termAux[-1] == '"':
            var = termAux.replace('"',"")
            res = self.get_positionals(var.split("|"))
        #Comprobamos si se debe realizar stemming
        elif (self.use_stemming):
            res = self.get_stemming(term, field)

        #Caso estándar
        elif (termAux in self.index):
            for t in self.index[termAux]:
                res = self.index[termAux]
        return res

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################



    def get_positionals(self, terms, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE POSICIONALES

        Devuelve  la posting list asociada a una secuencia de terminos consecutivos.

        param:  "terms": lista con los terminos consecutivos para recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        pos = -1
        docs = []
        res = []
        for i in terms:
            if i in self.posindex.keys():
                docs.append(list(sorted(self.posindex[i].keys())))
            else:
                return []
        prev = docs.pop(0)
        while docs != []:
            d = docs.pop(0)
            prev = self.and_posting(prev,d)
        for d in prev:
            posis = [self.posindex[w][d] for w in terms]

            for i in posis[0]:
                start = 1
                n = i
                while start <= len(posis):
                    if start == len(posis):
                        if d not in res:
                            res.append(d)
                            break
                        else: 
                            break
                    elif n+1 in posis[start]:
                        start += 1
                        n+=1
                    else:
                        break
        return res







    def get_stemming(self, term, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE STEMMING

        Devuelve la posting list asociada al stem de un termino.

        param:  "term": termino para recuperar la posting list de su stem.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        # Generamos el stem del término
        stem = self.stemmer.stem(term)
        res = []

        # Búscamos si el stem está indexado
        if (stem in self.sindex):
            # Devolvemos la posting list asociada al stem
            words = self.sindex[stem]
            for w in words:
                if w in self.index:
                    res = self.or_posting(res,self.index[w])


        return res


    def get_permuterm(self, term, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        Devuelve la posting list asociada a un termino utilizando el indice permuterm.

        param:  "term": termino para recuperar la posting list, "term" incluye un comodin (* o ?).
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        i=0
        res=[]
        resprov=[]
        if("*" in term):
            for simbolo in term:
                if(simbolo=="*"):
                    break
                i=i+1

            ini=term[0:i]
            fin=term[i+1:len(term)]
            for permuterms in self.ptindex.keys():
                if(permuterms[0]=="$"):
                    pterms=["",permuterms[1:]]
                elif(permuterms[len(permuterms)-1]=="$"):
                    pterms=[permuterms[:-1],""]
                else:
                    pterms=permuterms.split("$")
                if(pterms[0].endswith(fin) & pterms[1].startswith(ini)):
                    w=self.ptindex[permuterms]
                    if(w not in res):
                        resprov.append(w)
            
            for w in resprov:
                lista=self.get_posting(w)
                res=self.or_posting(res,lista)
        else:
            for simbolo in term:
                if(simbolo=="?"):
                    break
                i=i+1

            ini=term[0:i]
            fin=term[i+1:len(term)]

            for permuterms in self.ptindex.keys():
                if(permuterms[0]=="$"):
                    pterms=["",permuterms[1:]]
                elif(permuterms[len(permuterms)-1]=="$"):
                    pterms=[permuterms[:-1],""]
                else:
                    pterms=permuterms.split("$")
                if(pterms[0].endswith(fin) & pterms[1].startswith(ini)):
                    w=self.ptindex[permuterms]
                    if(w not in res and len(w)==len(term)):
                        resprov.append(w)
            for w in resprov:
                lista=self.get_posting(w)
                res=self.or_posting(res,lista)


            # #if permuterms.startswith(ini) and permuterms.endswith(fin):
            #    # l = self.get_posting(permuterms)
            #     for i in l:
            #         res.append(i)

        return res


    def reverse_posting(self, p):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Devuelve una posting list con todas las noticias excepto las contenidas en p.
        Util para resolver las queries con NOT.


        param:  "p": posting list


        return: posting list con todos los newid exceptos los contenidos en p

        """

        #Obtenemos una posting list con todas las noticias diferentes
        res = list(self.news.keys())

        #Procedemos a quitar aquellas que están incluidas en p

        return self.minus_posting(res, p)


        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################



    def and_posting(self, p1, p2):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el AND de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los newid incluidos en p1 y p2

        """
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################

        respuesta = []
        i = 0
        j = 0
        while len(p1)> i and len(p2)>j:
            if p1[i] == p2[j]:
                respuesta.append(p1[i])
                i = i + 1
                j = j + 1
            elif p1[i] < p2[j]:
                i = i + 1
            else:
                j = j + 1
        return respuesta



    def or_posting(self, p1, p2):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el OR de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los newid incluidos de p1 o p2

        """



        res=[]
        i=0
        j=0

        #mientras no acaben las posting list:
        while(i < len(p1) and j < len(p2)):
            #sii el elemento de p1 == p2:
            if(p1[i]==p2[j]):
                #se añade y avanzamos ambas posting list
                res.append(p1[i])
                i+=1
                j+=1
            #sii el elemento de p1 < p2:
            elif(p1[i]<p2[j]):
                #se añade y avanzamos ambas posting list
                res.append(p1[i])
                i+=1
            #sii el elemento de p2 <= p1:
            else:
                #se añade y avanzamos SOLO p2
                res.append(p2[j])
                j+=1

            #mientras no acaben las posting list se añaden a la variable res
        while(i<len(p1)):
                #se añade y avanzamos hasta finalizar
                res.append(p1[i])
                i+=1
        while(j<len(p2)):
                #se añade y avanzamos hasta finalizar
                res.append(p2[j])
                j+=1

        return res
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################


    def minus_posting(self, p1, p2):
        """
        OPCIONAL PARA TODAS LAS VERSIONES

        Calcula el except de dos posting list de forma EFICIENTE.
        Esta funcion se propone por si os es util, no es necesario utilizarla.

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los newid incluidos de p1 y no en p2

        """
        respuesta = []
        i = 0
        j = 0

        while len(p1)> i and len(p2)>j:
            if p1[i] == p2[j]:
                i = i + 1
                j = j + 1
            elif p1[i] < p2[j]:
                respuesta.append(p1[i])
                i = i + 1
            else:
                j = j + 1
        while(i<len(p1)):
            respuesta.append(p1[i])
            i+=1

        return respuesta

        ########################################################
        ## COMPLETAR PARA TODAS LAS VERSIONES SI ES NECESARIO ##
        ########################################################





    #####################################
    ###                               ###
    ### PARTE 2.2: MOSTRAR RESULTADOS ###
    ###                               ###
    #####################################


    def solve_and_count(self, query):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una consulta y la muestra junto al numero de resultados

        param:  "query": query que se debe resolver.

        return: el numero de noticias recuperadas, para la opcion -T

        """
        result = self.solve_query(query)
        print("%s\t%d" % (query, len(result)))
        return len(result)  # para verificar los resultados (op: -T)


    def solve_and_show(self, query):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una consulta y la muestra informacion de las noticias recuperadas.
        Consideraciones:

        - En funcion del valor de "self.show_snippet" se mostrara una informacion u otra.
        - Si se implementa la opcion de ranking y en funcion del valor de self.use_ranking debera llamar a self.rank_result

        param:  "query": query que se debe resolver.

        return: el numero de noticias recuperadas, para la opcion -T

        """
        
        result = self.solve_query(query)
        
            
        print(f"Noticias recuperadas: {len(result)}")
        for n in result:
            d = self.news[n]
            lis = d.split("_")
            ruta = self.docs[int(lis[0])]
            with open(ruta) as fi:
                docJson = json.load(fi)
                fecha = docJson[int(lis[1])]["date"]
                titulo = docJson[int(lis[1])]["title"]
                keywords = docJson[int(lis[1])]["keywords"]
                score = 0             
                print(f"Noticia: {n}")
                print(f"    Fecha: {fecha}")
                print(f"    Título: {titulo}")
                print(f"    Keywords: {keywords}")
                print(f"    Score: {score}")
                if self.show_snippet:
                    texto = docJson[int(lis[1])]["article"]
                    arrwords = self.tokenize(texto) 
                    consulta = query.lower()
                    #separamos los parentesis
                    split = ""
                    op = False
                    for i in range(0,len(query)):
                        item=consulta[i]
                        if item == '(' or item == ')':
                            split = split + " " + item + " "
                        else:
                            if item == '"':
                                op = not op
                            if item == " " and open:
                                split = split + "|"
                            else: split = split + item
                            
                    

                    #separamos los diferentes items de la query
                    consulta = split.split(" ")  
                    palabras = []
                    for i in range(len(consulta)):
                        if consulta[i] == "not":
                            i = i + 1
                        else:
                            if consulta[i]!= "or" and consulta[i] != "and":
                                palabras.append(consulta[i])
                    snippet =""
                    encontradas = 0
                    abuscar = []

                    if self.use_stemming:
                        for p in palabras:
                            terminos=self.sindex[self.stemmer.stem(p)]
                            for t in terminos:
                                abuscar.append(t)
                    
                    else:
                        for p in palabras:
                            if("*" in p or "?" in p):
                                i=0
                                res=[]
                                p = p.replace("?", "*")

                                for simbolo in p:
                                    if(simbolo=="*"):
                                        break
                                    i=i+1
                                ini=p[0:i]
                                fin=p[i+1:len(p)]
                                for permuterms in self.ptindex:
                                    if permuterms.startswith(ini) and permuterms.endswith(fin):
                                        abuscar.append(permuterms)
                            elif('"' in p):
                                words = p.replace('"',"").replace('|'," ")
                                abuscar.append(words)
                            else:
                                abuscar.append(p)
                                 
                    if len(abuscar) > 1:
                        for w in arrwords:
                            if w in abuscar:
                                encontradas += 1
                                snippet =  snippet + " " + w
                                if len(snippet.split(" ")) > 10: break
                            else:
                                if encontradas > 0 and encontradas != len(abuscar):
                                    snippet = snippet + " " + w
                                    
                    if len(abuscar) == 1 or len(snippet.split(" ")) < 10 or len(snippet.split(" ")) > 250:
                        
                        puntos = texto.lower().split(".")
                        for f in puntos:
                            for i in abuscar:
                                if i in f:
                                    snippet = f
                    
                    print(f"    Snippet: {snippet}")
                    print("---------------------------------------------------------------------------------")
                    
                            
                            

    def rank_result(self, result, query):
        """
        NECESARIO PARA LA AMPLIACION DE RANKING
        Ordena los resultados de una query.
        param:  "result": lista de resultados sin ordenar
                "query": query, puede ser la query original, la query procesada o una lista de terminos
        return: la lista de resultados ordenada
        """

        pass

        ###################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE RANKING ##
        ###################################################