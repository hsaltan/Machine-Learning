# AI-Powered CV Screener

This tool screens and analyzes CVs, scoring them with respect to a job description on a scale from 0 to 10.

Features include:
- Two file uploaders to upload both the CV and the job description.
- Analysis of the CV document to provide a suitability score.
- Display of keywords extracted from the job description, highlighting their presence in the CV.
- An option to save selected CVs and store them in a user-dedicated S3 bucket on AWS.

## Preparation

Before deploying the app, please complete the following preliminary steps:

- Create an AWS account if you do not already have one.
- [Configure](https://docs.aws.amazon.com/cli/latest/reference/configure/) your AWS profile in the region where you intend to deploy your app.
- Create an OpenAI account if you do not already have one.
- Generate an OpenAI API key if you do not already have one.

## Deployment

Follow these steps to deploy the app:
1. Create a bucket with a unique name in AWS to serve as the *application files* bucket.
2. Upload the three files (`cvanalyzer.py`, `web_app.py`, `HR_image_1.png`) to the *application files* bucket.
3. Create another bucket with a unique name for storing selected CVs; this will be your *cv files* bucket. In the `web_app.py file`, replace the placeholder for the *cv files* bucket name with your specific bucket name.
4. Define a secure string parameter for the OpenAI API key using the Parameter Store in AWS Systems Manager.
5. Create the following IAM policy: `CVScreenerPolicy`,

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:DescribeParameters"
            ],
            "Resource": "arn:aws:ssm:us-east-1:<YOUR-ACCOUNT-ID>:parameter/<YOUR-OPENAI-KEY-PARAM>"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameters",
                "ssm:GetParameter"
            ],
            "Resource": "arn:aws:ssm:us-east-1:<YOUR-ACCOUNT-ID>:parameter/<YOUR-OPENAI-KEY-PARAM>"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:List*",
                "s3:Get*",
                "s3:Put*"
            ],
            "Resource": [
                "arn:aws:s3:::<YOUR-APP-FILES-BUCKET>",
                "arn:aws:s3:::<YOUR-APP-FILES-BUCKET>/*",
                "arn:aws:s3:::<YOUR-CV-FILES-BUCKET>",
                "arn:aws:s3:::<YOUR-CV-FILES-BUCKET>/*"
            ]
        }
    ]
}
```
6. Create an IAM role named `CVScreenerRole`.
7. Attach the policy `CVScreenerPolicy` to the role `CVScreenerRole`.
8. Launch an EC2 instance with the following specifications:
    - Choose Ubuntu 24.04 as the AMI.
    - Select t2.micro as the instance type.
    - Configure the security group to allow inbound traffic on ports 80, 443, and 8501 (Streamlit runs on port 8501).
    - Assign `CVScreenerRole` as the IAM instance profile.
9. Once the EC2 instance is ready, SSH into it and execute the following commands in the specified order:

```
sudo apt-get update
sudo apt install tmux
sudo apt install python3-pip -y
sudo apt install python3-venv -y
sudo mkdir cv-app

cd cv-app
python3 -m venv myenv
source myenv/bin/activate
pip install openai 
pip install pdfplumber 
pip install gensim 
pip install streamlit 
pip install python-docx 
pip install boto3 
pip install awscli
aws s3 cp s3://<YOUR-APPLICATION-FILES-BUCKET-NAME>/ . --recursive

deactivate
cd ..
tmux new -s streamlit_session
cd cv-app
source myenv/bin/activate
streamlit run web_app.py --server.maxUploadSize=1
```
We limit the upload size to 1 MB per file, which is sufficient for most documents. Adjust this limit by assigning a higher value in the Streamlit command if necessary.

## Troubleshooting

If you encounter any issues while using the program:
- If the page does not load as expected, try refreshing it.
- If the app does not return results as expected, attempt to re-run it.

These steps typically resolve most issues.
