# Splunk .conf21
## Secrets from the Developer Kitchen - Develop on Splunk like a Pro with UCC, Visual Studio Code, and Git

https://conf.splunk.com/learn/session-scheduler.html?search=dev1147c

This is a sample repository that accompanies the [Splunk .conf21 DEV1147C Session](https://conf.splunk.com/learn/session-scheduler.html?search=dev1147c).  The repository contains examples for using Splunk’s Universal Configuration Console, Microsoft Visual Stuido Code with the Splunk extension, and GitHub workflow actions.

## Resources

* [Universal Configuration Console (UCC)](https://github.com/splunk/addonfactory-ucc-generator) - UCC is a framework to generate UI-based Splunk Add-ons. It includes UI, Rest handler, Modular input, Oauth, Alert action templates.
* [globalConfig.json Schema](https://raw.githubusercontent.com/splunk/addonfactory-ucc-base-ui/main/src/main/webapp/schema/schema.json) - globalConfig.json defines the UI for add-ons.
* [Splunk Packaging Toolkit](https://dev.splunk.com/enterprise/docs/releaseapps/packageapps/packagingtoolkit/) - used to package an app for distribution, regardless of physical placement.
* [Splunk Visual Studio Code Extension](https://marketplace.visualstudio.com/items?itemName=Splunk.splunk) - this extension has snippets and validators for globalConfig.json.  The extension also contains intelligence for Splunk .conf files (inline documentation, auto-complete, validation, etc.) as well as debugging capabilities for Splunk modular inputs, custom REST handlers, custom search commands, etc.
* [Splunk Visual Studio Code Supporting Add-on](https://splunkbase.splunk.com/app/4801/) - enables code running in Splunk to be debugged by Visual Stuido Code.
