# How to Contribute

:+1::tada: First off, thanks for taking the time to contribute! :tada::+1:

Following these guidelines helps keep the project maintainable, easy to contribute to, and more secure.
Thank you for taking the time to read this. Thank you for taking the time to follow this guide.

## Where To Start

There are many ways to contribute.
You can fix a bug, improve the documentation, submit feature requests and issues, or work on a feature you need for yourself.

Pull requests are necessary for all contributions of code or documentation.
If you are new to open source and not sure what a pull request is ... welcome, we're glad to have you!
All of us once had a contribution to make and didn't know where to start.

Even if you don't write code for your job, don't worry, the skills you learn during your first contribution to open source can be applied in so many ways, you'll wonder what you ever did before you had this knowledge.

Here are a few resources on how to contribute to open source for the first time.

- [First Contributions](https://github.com/firstcontributions/first-contributions/blob/master/README.md)
- [Public Learning Paths](https://lab.github.com/githubtraining/paths)

## Pull Requests

If you want to contribute to the project, go through the process
of making a fork and pull request yourself:

> 1. Create your own fork of the code
> 2. Clone the fork locally
> 3. Make the changes in your local clone
> 4. Push the changes from local to your fork
> 5. Create a pull request to pull the changes from your fork back into the
>    upstream repository

Please use clear commit messages so we can understand what each commit does.
We'll review every PR and might offer feedback or request changes before
merging.

- Validate your code using `pylint` as per below, and test your changes
- We might offer feedback or request modifications before merging

```
pylint pc_lib/*.py pc_lib/*/*.py scripts/*.py
```

## Validate your code before submitting

```
python3 -m virtualenv venv && source venv/bin/activate
pip install -r requirements.txt
pip install flake8
pip install black
flake8 $(git ls-files '*.py')
black $(git ls-files '*.py') --line-length=127
```