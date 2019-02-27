
def sendMsg(StartBuild){

    String color
    ArrayList message = new ArrayList()
    message.add(String.format('%1$s - #%2$s', env.JOB_NAME.replace('%2F', '/'), env.BUILD_NUMBER))
    String grey = '#948f8f'

    if (StartBuild){
        color = grey
        message.add('Started')
    }else{
        String result = currentBuild.result.substring(0,1) + currentBuild.result.substring(1).toLowerCase()
        message.add(String.format('%1$s after %2$s', result, currentBuild.durationString.replace(' and counting', '')))
        switch(currentBuild.result) {
            case "SUCCESS":
                color = 'good'
                break
            case "FAILURE":
                color = 'danger'
                break
            case "UNSTABLE":
                color = 'warning'
                break
            default:
                color = grey
        }
    }

    message.add(String.format('(<%1$s|%2$s>)', env.BUILD_URL, 'Open'))
    
    try{
        timeout(time: 15, unit: 'SECONDS') {
            slackSend color: color, failOnError: true, message: message.join(' ')
        }
    }catch (exception){
        showError(exception)
    }

}

def showError(exception) {
    ansiColor('xterm') {
        echo('\u001B[31m' + exception.getMessage() + '\u001B[0m')
    }
}

currentBuild.result = "SUCCESS"

node(){
    timeout(time: 5) {
        timestamps {
            sendMsg(true)
            properties([disableConcurrentBuilds(),
                        buildDiscarder(logRotator(artifactDaysToKeepStr: '',
                                                  artifactNumToKeepStr: '',
                                                  daysToKeepStr: '',
                                                  numToKeepStr: '10'))])
            try {
                cleanWs(cleanWhenAborted: false, cleanWhenFailure: false, cleanWhenNotBuilt: false)
                stage('Checkout'){
                    checkout scm
                }
                stage('RunTests'){
                    bat script: '''virtualenv venv
                                start venv\\Scripts\\activate.bat
                                venv\\Scripts\\pip install -e %WORKSPACE% 
                                venv\\Scripts\\runner1c sync --create --folder %WORKSPACE%/runner1c
                                venv\\Scripts\\pytest --log-file=pylog.txt --junitxml=junitxml.xml --cov=runner1c runner1c/tests/ --cov-report xml:cov.xml
                                exit 0'''
                }
                stage('GetResult'){
                    cobertura(autoUpdateHealth: false,
                            autoUpdateStability: false,
                            coberturaReportFile: 'cov.xml',
                            failUnhealthy: false,
                            failUnstable: false,
                            maxNumberOfBuilds: 0,
                            onlyStable: false,
                            zoomCoverageChart: false)
                    junit('junitxml.xml')
                }
            } catch (exception) {
                showError(exception)
                currentBuild.result = "FAILURE"
            } finally {
                sendMsg(false)
            }
        }
    }
}