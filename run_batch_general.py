import json
import boto3
import string
import os
import posixpath
class JobQueue():

    def __init__(self,name=None):
        self.sqs = boto3.resource('sqs')
        self.queue = self.sqs.get_queue_by_name(QueueName=name+'Queue')
        self.inProcess = -1
        self.pending = -1

    def scheduleBatch(self, data):
        msg = json.dumps(data)
        response = self.queue.send_message(MessageBody=msg)
        print('Batch sent. Message ID:',response.get('MessageId'))

#project specific stuff
topdirname='' #PROJECTNAME        
projectname='' #PROJECTNAME
batchsuffix='' #BATCHNAME
rows=list(string.ascii_uppercase)[0:16]
columns=range(1,25)
sites=range(1,10)
platelist=[] # PLATEFOLDERNAMES
zprojpipename='Zproj.cppipe'
illumpipename='illum.cppipe'
qcpipename='qc.cppipe'
assaydevpipename='assaydev.cppipe'
analysispipename='analysis.cppipe'
batchpipenamezproj='Batch_data_zproj.h5'
batchpipenameillum='Batch_data_illum.h5'
batchpipenameqc='Batch_data_qc.h5'
batchpipenameassaydev='Batch_data_assaydev.h5'
batchpipenameanalysis='Batch_data_analysis.h5'

#not project specific, unless you deviate from the structure
startpath=posixpath.join('projects',topdirname)
pipelinepath=posixpath.join(startpath,os.path.join('workspace/pipelines',batchsuffix))
zprojoutpath=posixpath.join(startpath,os.path.join(batchsuffix,'images'))
zprojoutputstructure="Metadata_Plate"
illumoutpath=posixpath.join(startpath,os.path.join(batchsuffix,'illum'))
QCoutpath=posixpath.join(startpath,os.path.join('workspace/qc',os.path.join(batchsuffix,'results')))
assaydevoutpath=posixpath.join(startpath,os.path.join('workspace/assaydev',batchsuffix))
analysisoutpath=posixpath.join(startpath,os.path.join('workspace/analysis',batchsuffix))
inputpath=posixpath.join(startpath,os.path.join('workspace/qc',os.path.join(batchsuffix,'rules')))
datafilepath=posixpath.join(startpath,os.path.join('workspace/load_data_csv',batchsuffix))
anlysisoutputstructure="Metadata_Plate/analysis/Metadata_Plate-Metadata_Well-Metadata_Site"
batchpath=posixpath.join(startpath,os.path.join('workspace/batchfiles',batchsuffix))

def MakeZprojJobs(batch=False):
    zprojqueue = JobQueue(projectname+'_Zproj')
    for tozproj in platelist:
        for eachrow in rows:
            for eachcol in columns:
                for eachsite in sites:
                    if not batch:
                        templateMessage_zproj = {'Metadata': 'Metadata_Plate='+tozproj+',Metadata_Well='+eachrow+'%02d' %eachcol+',Metadata_Site='+str(eachsite),
                                        'pipeline': posixpath.join(pipelinepath,zprojpipename),
                                        'output': zprojoutpath,
                                        'output_structure': zprojoutputstructure,
                                        'input': inputpath,
                                        'data_file': posixpath.join(datafilepath,tozproj,'load_data.csv')
                                        }
                    else:
                        templateMessage_zproj = {'Metadata': 'Metadata_Plate='+tozproj+',Metadata_Well='+eachrow+'%02d' %eachcol+',Metadata_Site='+str(eachsite),
                                        'pipeline': posixpath.join(batchpath,batchpipenamezproj),
                                        'output': zprojoutpath,
                                        'output_structure': zprojoutputstructure,
                                        'input': inputpath,
                                        'data_file': posixpath.join(batchpath,batchpipenamezproj)
                                        }

                    zprojqueue.scheduleBatch(templateMessage_zproj)

    print('Z projection job submitted. Check your queue')

def MakeIllumJobs(batch='false'):    
    illumqueue = JobQueue(projectname+'_Illum')
    for toillum in platelist:
        if not batch:
            templateMessage_illum = {'Metadata': 'Metadata_Plate='+toillum,
                                     'pipeline': posixpath.join(pipelinepath,illumpipename),
                                     'output': illumoutpath,
                                     'input': inputpath, 
                                     'data_file':posixpath.join(datafilepath,toillum,'load_data.csv')}            
        else:
            templateMessage_illum = {'Metadata': 'Metadata_Plate='+toillum,
                                        'pipeline': posixpath.join(batchpath,batchpipenameillum),
                                        'output': illumoutpath,
                                        'input':inputpath,
                                        'data_file': posixpath.join(batchpath,batchpipenameillum)
                                        }
            
        illumqueue.scheduleBatch(templateMessage_illum)

    print('Illum job submitted. Check your queue')

def MakeQCJobs(batch=False):
    qcqueue = JobQueue(projectname+'_QC')
    for toqc in platelist:
        for eachrow in rows:
            for eachcol in columns:
                if batch==False:
                    templateMessage_qc = {'Metadata': 'Metadata_Plate='+toqc+',Metadata_Well='+eachrow+'%02d' %eachcol,
                                    'pipeline': posixpath.join(pipelinepath,qcpipename),
                                    'output': QCoutpath,
                                    'input': inputpath,
                                    'data_file': posixpath.join(datafilepath,toqc,'load_data.csv')
                                    }
                else:
                    templateMessage_qc = {'Metadata': 'Metadata_Plate='+toqc+',Metadata_Well='+eachrow+'%02d' %eachcol,
                                    'pipeline': posixpath.join(batchpath,batchpipenameqc),
                                    'output': QCoutpath,
                                    'input': inputpath,
                                    'data_file': posixpath.join(batchpath,batchpipenameqc)
                                }
                qcqueue.scheduleBatch(templateMessage_qc)

    print('QC job submitted. Check your queue')

def MakeQCJobs_persite(batch=False):
    qcqueue = JobQueue(projectname+'_QC')
    for toqc in platelist:
        for eachrow in rows:
            for eachcol in columns:
                for eachsite in sites:
                    if batch==False:
                        templateMessage_qc = {'Metadata': 'Metadata_Plate='+toqc+',Metadata_Well='+eachrow+'%02d' %eachcol+',Metadata_Site='+str(eachsite),
                                        'pipeline': posixpath.join(pipelinepath,qcpipename),
                                        'output': QCoutpath,
                                        'input': inputpath,
                                        'data_file': posixpath.join(datafilepath,toqc,'load_data.csv')
                                        }
                    else:
                        templateMessage_qc = {'Metadata': 'Metadata_Plate='+toqc+',Metadata_Well='+eachrow+'%02d' %eachcol+',Metadata_Site='+str(eachsite),
                                        'pipeline': posixpath.join(batchpath,batchpipenameqc),
                                        'output': QCoutpath,
                                        'input': inputpath,
                                        'data_file': posixpath.join(batchpath,batchpipenameqc)
                                        }

                    qcqueue.scheduleBatch(templateMessage_qc)

    print('QC job submitted. Check your queue')

def MakeAssayDevJobs(batch=False):
    assaydevqueue = JobQueue(projectname+'_AssayDev')
    for toad in platelist:
        for eachrow in rows:
            for eachcol in columns:
                if batch==False:
                    templateMessage_ad = {'Metadata': 'Metadata_Plate='+toad+',Metadata_Well='+eachrow+'%02d' %eachcol,
                                    'pipeline': posixpath.join(pipelinepath,assaydevpipename),
                                    'output': assaydevoutpath,
                                    'input': inputpath,
                                    'data_file': posixpath.join(datafilepath,toad,'load_data.csv')
                                    }
                else:
                    templateMessage_ad = {'Metadata': 'Metadata_Plate='+toad+',Metadata_Well='+eachrow+'%02d' %eachcol,
                                    'pipeline': posixpath.join(batchpath,batchpipenameassaydev),
                                    'output': assaydevoutpath,
                                    'input': inputpath,
                                    'data_file': posixpath.join(batchpath,batchpipenameassaydev)
                                }
                assaydevqueue.scheduleBatch(templateMessage_ad)

    print('AssayDev job submitted. Check your queue')

def MakeAnalysisJobs(batch=False):
    analysisqueue = JobQueue(projectname+'_Analysis')
    for toanalyze in platelist:
        for eachrow in rows:
            for eachcol in columns:
                for eachsite in sites:
                    if batch==False:
                        templateMessage_analysis = {'Metadata': 'Metadata_Plate='+toanalyze+',Metadata_Well='+eachrow+'%02d' %eachcol+',Metadata_Site='+str(eachsite),
                                        'pipeline': posixpath.join(pipelinepath,analysispipename),
                                        'output': analysisoutpath,
                                        'output_structure':anlysisoutputstructure,
                                        'input':inputpath,
                                        'data_file': posixpath.join(datafilepath,toanalyze,'load_data_with_illum.csv')
                                        }                        
                    else:
                        templateMessage_analysis = {'Metadata': 'Metadata_Plate='+toanalyze+',Metadata_Well='+eachrow+'%02d' %eachcol+',Metadata_Site='+str(eachsite),
                                        'pipeline': posixpath.join(batchpath,batchpipenameanalysis),
                                        'output': analysisoutpath,
                                        'output_structure':anlysisoutputstructure,
                                        'input':inputpath,
                                        'data_file': posixpath.join(batchpath,batchpipenameanalysis)
                                        }

                    analysisqueue.scheduleBatch(templateMessage_analysis)

    print('Analysis job submitted. Check your queue')

#MakeZprojJobs(batch=False)    
#MakeIllumJobs(batch=False)
#MakeQCJobs(batch=False)
#MakeQCJobs_persite(batch=False)
#MakeAssayDevJobs
#MakeAnalysisJobs(batch=False)

