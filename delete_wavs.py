import boto3

# Initialize a session using AWS CLI configuration
session = boto3.Session()

# Create an S3 client
s3 = session.client('s3')

# ask for the interview id from the user
interview_id = input("Enter the interview ID: ")

prefix = f"Processed/{interview_id}/"
bucket_name = 'storycorps-signature-remote'

#confirm the user wants to delete the files
print(f"Are you sure you want to delete all .wav files in the {prefix} directory?")
confirm = input("Enter 'yes' to confirm: ")
if confirm.lower() != 'yes':
    print("Exiting...")
    exit()

print(f"Deleting .wav files in {prefix} directory...")

# List and delete .wav files
def delete_wav_files(bucket, prefix):
    try:
        # List all files in the specified directory
        objects = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if 'Contents' in objects:
            for obj in objects['Contents']:
                file_name = obj['Key']
                if file_name.endswith('.wav'):
                    # Delete the file
                    s3.delete_object(Bucket=bucket, Key=file_name)
                    print(f"Deleted {file_name}")
        
        print("Deletion complete")

    except Exception as e:
        print(f"Error: {e}")


# Call the function
delete_wav_files(bucket_name, prefix)