
def function 
node('built-in') {
    copyArtifacts filter: 'lib.groovy', fingerprintArtifacts: true, flatten: true, projectName: 'ScriptForStartBuild'
    function = fileLoader.load('lib.groovy')
}
function.setScript(this)

currentBuild.result = "SUCCESS"

node(){
    timeout(time: 5) {
        timestamps {
            function.sendMsg(true)
            properties([disableConcurrentBuilds(),
                        buildDiscarder(logRotator(artifactDaysToKeepStr: '',
                                                  artifactNumToKeepStr: '',
                                                  daysToKeepStr: '',
                                                  numToKeepStr: '10'))])
            try {
                cleanWs(cleanWhenAborted: false, cleanWhenFailure: false, cleanWhenNotBuilt: false)
                
                stage('Checkout'){
                    def scmVars = checkout(scm)
                    repo_from_scm = scmVars.GIT_URL.tokenize('/.')[-2]
                }
                
                stage('RunTests'){
                    
                    bat script: '''virtualenv venv
                                start venv\\Scripts\\activate.bat
                                venv\\Scripts\\pip install -e %WORKSPACE% 
                                venv\\Scripts\\runner1c sync --create --folder %WORKSPACE%/runner1c
                                venv\\Scripts\\pytest --log-file=pylog.txt --junitxml=junitxml.xml --cov=runner1c runner1c/tests/ --cov-report xml:cov.xml
                                exit 0'''
                    
                    def scannerHome = tool(name: 'sonar', type: 'hudson.plugins.sonar.SonarRunnerInstallation')
                    withSonarQubeEnv(installationName: 'sonar') {
                        bat String.format('%s/bin/sonar-scanner -Dsonar.branch.name=%s -Dsonar.projectKey=%s', scannerHome, env.BRANCH_NAME, repo_from_scm)
                    }

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
                function.setResultAfterError(exception)
            } finally {
                function.sendMsg(false)
            }
        }
    }
}