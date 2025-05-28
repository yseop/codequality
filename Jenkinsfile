#! /usr/bin/env groovy

@Library('Utilities') _

pipeline {
    agent {
        node {
            label 'python'
        }
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '5', artifactNumToKeepStr: '5'))
    }

    environment {
        SLACK_NOTIFY = utils.getAuthorSlackHandle()
    }

    stages {
        stage('Abort previous build') {
            steps {
                script {
                    utils.killPreviousBuilds()
                }
            }
        }

        stage('Checks') {
            parallel {
                stage('Bash generator') {
                    steps {
                        sh './bash/generator/tests/run.sh --uv'
                    }
                }

                stage('AsciiDoc syntax') {
                    steps {
                        /*
                         * Try to compile every AsciiDoc file,
                         * and yell if there are warnings.
                         */
                        sh '''
                            find . -type f '(' \
                                    -iname '*.ad' -or \
                                    -iname '*.adoc' -or \
                                    -iname '*.asciidoc' \
                                    ')' -print0 |
                                    xargs -0n 1 --verbose asciidoctor \
                                            --failure-level warn \
                                            --out-file /dev/null
                        '''
                    }
                }
            }
        }
    } // ↖ stages

    post {
        success {
            slackSend color: 'good', message: "SUCCESSFUL: Job “<${env.BUILD_URL}|${env.JOB_NAME} [${env.BUILD_NUMBER}]>” <@${SLACK_NOTIFY}>"
        }

        failure {
            slackSend color: 'danger', message: "FAILED: Job “<${env.BUILD_URL}|${env.JOB_NAME} [${env.BUILD_NUMBER}]>” <@${SLACK_NOTIFY}>"
        }

        cleanup {
            // Clean up our workspace.
            cleanWs deleteDirs: true
            deleteDir()
        }
    }
}
