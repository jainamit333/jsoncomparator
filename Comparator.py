from flask import Flask, render_template,url_for,request,json
from pip._vendor import requests
from collections import defaultdict

app = Flask(__name__)

@app.route('/')
def index():
        return render_template('index.html')

@app.route('/jest')
def testjson():
    data = open('/home/amit/Downloads/data1.json')
    data = json.load(data)
    output = []
    for d in data:

        for t in d:
            print d[t]
            output['text'] = d[t]

    return render_template('comparejson.html',datajson = data)



@app.route('/compareflightfileupload',methods=['POST'])
def comparewithfile():
    resultToShow = []
    url1 = request.files['url1']
    url2  = request.files['url2']
    data1 = loadFileFromUpload(url1)
    data2 = loadFileFromUpload(url2)
    services = request.form['service']
    data1 = nestedScooper(data1,request.form['scoop_id_1'],request.form['scoop_1'])
    data2 = nestedScooper(data2,request.form['scoop_id_2'],request.form['scoop_2'])
    data1 = convertListToDic(data1, request.form['dictionary_id_1'],request.form['appender_1'],services)
    data2 = convertListToDic(data2, request.form['dictionary_id_2'],request.form['appender_2'],services)
    startFlightSearchComparision(data1,data2,convertStringToList(request.form['attrs'],","),resultToShow,len(request.form['attrs']))
    return render_template('result.html',data = resultToShow)



@app.route('/compareflight',methods=['POST'])
def compareFlights():
    resultToShow = []
    url1 = request.form['url1']
    url2  = request.form['url1']
    data1 = loadFileFromUrl(url1)
    data2 = loadFileFromUrl(url2)
    services = request.form['service']
    data1 = nestedScooper(data1,request.form['scoop_id_1'],request.form['scoop_1'])
    data2 = nestedScooper(data2,request.form['scoop_id_2'],request.form['scoop_2'])
    data1 = convertListToDic(data1, request.form['dictionary_id_1'],request.form['appender_1'],services)
    data2 = convertListToDic(data2, request.form['dictionary_id_2'],request.form['appender_2'],services)

    startFlightSearchComparision(data1,data2,convertStringToList(request.form['attrs'],","),resultToShow,len(request.form['attrs']))
    return render_template('result.html',data = resultToShow)


def convertStringToList(param,splitter):
    return param.split(splitter)

def convertListToDic(data,id,appender,service):

    dictionary = {}
    for value in data:
        if len(service) > 0 :
            if (value[id].lower()).find(service.lower()) != -1:
                key = generateKey(value[id],appender)
                dictionary[key] = value
        else:
            key = generateKey(value[id],appender)
            dictionary[key] = value

    return dictionary

def generateKey(value,appender):
    if appender == 'REM_AFTER_LAST_UNDERSCORE' :
        value = value[0:value.rindex("_")]
        return value.lower()
    if appender == 'NOTHING':
        return value.lower()


def startFlightSearchComparision(json1,json2,listOfAttributes,resultToShow,attrLen):

    for json in json1:
        data1 = json1[json]
        data2 = json2[json]
        #add key to the result for showing
        compareMappedJson(data1,data2,listOfAttributes,json,resultToShow,attrLen)


def compareMappedJson(data1,data2,listOfAttributes,jsonId,resultToShow,attrLen):

    if attrLen == 0:
        compareCompleteJsonKeyByKey(data1,data2,jsonId,resultToShow)
        return

    for attribute in listOfAttributes:
        counter = 0
        attributeRail = convertStringToList(attribute,".")
        validForCompare = False
        value1 = ""
        value2 = ""
        for attr in attributeRail:

            value1 = data1[attr]
            value2 = data2[attr]
            counter += 1
            if isinstance(value1,list) & isinstance(value2,list):
                simpleBlindNestedComparator(value1,value2,computeAttrList(attributeRail,counter),jsonId,resultToShow)
                validForCompare = False
                break
            else:
                if isinstance(value1,list) & ( not isinstance(value2,list)):
                    resultToShow.append("Data Type Mismatch found for "+ attributeRail+" - "+attr+" --- " + " for id :-" + jsonId)
                    validForCompare = False
                    break
                else:
                    if isinstance(value1,list) & ( not isinstance(value2,list)):
                        resultToShow.append("Data Type Mismatch found for "+ attributeRail+" - "+attr+" --- " + " for id :-" + jsonId)
                        validForCompare = False
                        break
                    else:
                        validForCompare = True


        if validForCompare:
            compareActualValue(value1,value2,attribute,jsonId,resultToShow)


def simpleBlindNestedComparator(json1,json2,attributes,jsonId,resultToShow):

    if len(attributes) == 0:
        if json1 != json2:
            resultToShow.append("Value is not same : "+ attributes+ " -- " +jsonId)
    else:
        listCounter = 0
        for valueOfFirst in json1:
            valueForSecond = json2[listCounter]
            listCounter = listCounter+1
            recalculateAttibute = [".".join(attributes)]
            compareMappedJson(valueOfFirst,valueForSecond,recalculateAttibute,jsonId,resultToShow)


def compareCompleteJsonKeyByKey(data1,data2,jsonId,resultToShow):
    int = 0
    for data in data1:
        print data
        if isinstance(data,dict):
            compareActualValue(data1[int],data2[int],"",jsonId,resultToShow)
            continue
        value1 = data1[data]
        value2 = data2[data]
        if isinstance(value1,list) & isinstance(value2,list):
            compareCompleteJsonKeyByKey(value1,value2,jsonId,resultToShow)
        else:
            if (not isinstance(value1,list)) & isinstance(value2,list):
                resultToShow.insert(len(resultToShow),"DataType mismatch for attribute "+ data)
            else:
                if (not isinstance(value2,list)) & isinstance(value1,list):
                    resultToShow.insert(len(resultToShow),"DataType mismatch for attribute "+ data)
                else:
                    compareActualValue(value1,value2,data,jsonId,resultToShow)



def computeAttrList(currentList,indexTillAlreadyExecuted):
    return currentList[indexTillAlreadyExecuted:]


def compareActualValue(value1,value2,completeAttrinbute,jsonId,resultToShow):

    if value1 != value2:
        resultToShow.insert(len(resultToShow),"Value is not same : "+ str(completeAttrinbute) + " - "+str(value1)+" --- "+str(value2)+" for :- "+jsonId)


def loadFileFromUrl(url):
    try:
        uResponse = requests.get(url)
    except requests.ConnectionError:
        return "Connection Error"
    Jresponse = uResponse.text
    data = json.loads(Jresponse)
    return data

def loadFileFromUpload(file):
    data = file.read()
    data = json.loads(data);
    return data


def nestedScooper(data,indexOfData,attrs):
    if len(attrs) > 0 :
        attrs = attrs.split(".")
        data = data[int(indexOfData)]
        for att in attrs:
            data = data[att]
        return data
    else:
        return data

def sortJson(data,attr,reversetrue):
    data =  sorted(data,key=lambda k:k.get(attr),reverse=reversetrue)
    return data



if __name__ == '__main__':
    app.run(debug=True)
