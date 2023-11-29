import json
from dateutil import parser as date_parser
from ..utils import constants


def save_json_output(repo_data, out_path, missing, pretty=False):
    """
    Function that saves the final json Object in the output file
    Parameters
    ----------
    @param repo_data: dictionary with the metadata to be saved
    @param out_path: output path where to save the JSON
    @param missing: print the categories SOMEF was not able to find
    @param pretty: format option to print the JSON in a human-readable way

    Returns
    -------
    @return: Does not return a value
    """
    print("Saving json data to", out_path)
    if missing:
        # add a new key-value papir to the dictionary
        repo_data[constants.CAT_MISSING] = create_missing_fields(repo_data)
    with open(out_path, 'w') as output:
        if pretty:
            json.dump(repo_data, output, sort_keys=True, indent=2)
        else:
            json.dump(repo_data, output)


def save_codemeta_output(repo_data, outfile, pretty=False):
    """
    Function that saves a Codemeta JSONLD file with a summary of the results

    Parameters
    ----------
    @param repo_data: JSON with the results to translate to Codemeta
    @param outfile: path where to save the codemeta file
    @param pretty: option to show the JSON results in a nice format
    """

    def format_date(date_string):
        date_object = date_parser.parse(date_string)
        return date_object.strftime("%Y-%m-%d")

    # latest_release = None
    # releases = data_path(["releases", "excerpt"])
    #
    # if releases is not None and len(releases) > 0:
    #     latest_release = releases[0]
    #     latest_pub_date = date_parser.parse(latest_release["datePublished"])
    #     for index in range(1, len(releases)):
    #         release = releases[index]
    #         pub_date = date_parser.parse(release["datePublished"])
    #
    #         if pub_date > latest_pub_date:
    #             latest_release = release
    #             latest_pub_date = pub_date

    # def release_path(path):
    #     return DataGraph.resolve_path(latest_release, path)

    code_repository = None
    if constants.CAT_CODE_REPOSITORY in repo_data:
        code_repository = repo_data[constants.CAT_CODE_REPOSITORY][0][constants.PROP_RESULT][constants.PROP_VALUE]

    author_name = None
    if constants.CAT_OWNER in repo_data:
        author_name = repo_data[constants.CAT_OWNER][0][constants.PROP_RESULT][constants.PROP_VALUE]

    descriptions = repo_data[constants.CAT_DESCRIPTION]
    descriptions_text = []
    if descriptions is not None:
        descriptions.sort(key=lambda x: (x[constants.PROP_CONFIDENCE] + (1 if x[constants.PROP_TECHNIQUE] == constants.GITHUB_API else 0)),
                          reverse=True)
        descriptions_text = [x[constants.PROP_RESULT]
                             [constants.PROP_VALUE] for x in descriptions]

    codemeta_output = {
        "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
        "@type": "SoftwareSourceCode"
    }
    if constants.CAT_LICENSE in repo_data:
        # We mix the name of the license from github API with the URL of the file (if found)
        l_result = {}
        for l in repo_data[constants.CAT_LICENSE]:
            if constants.PROP_NAME in l[constants.PROP_RESULT].keys():
                l_result["name"] = l[constants.PROP_RESULT][constants.PROP_NAME]
            if "url" not in l_result.keys() and constants.PROP_URL in l[constants.PROP_RESULT].keys():
                l_result["url"] = l[constants.PROP_RESULT][constants.PROP_URL]
            # We get the first license we find from the repo
            elif l[constants.PROP_TECHNIQUE] == constants.TECHNIQUE_FILE_EXPLORATION \
                    and constants.PROP_SOURCE in l.keys() and "api.github.com" in l_result["url"]:
                l_result["url"] = l[constants.PROP_SOURCE]
        codemeta_output["license"] = l_result
    if code_repository is not None:
        codemeta_output["codeRepository"] = code_repository
        codemeta_output["issueTracker"] = code_repository + "/issues"
    if constants.CAT_DATE_CREATED in repo_data:
        codemeta_output["dateCreated"] = format_date(
            repo_data[constants.CAT_DATE_CREATED][0][constants.PROP_RESULT][constants.PROP_VALUE])
    if constants.CAT_DATE_UPDATED in repo_data:
        codemeta_output["dateModified"] = format_date(
            repo_data[constants.CAT_DATE_UPDATED][0][constants.PROP_RESULT][constants.PROP_VALUE])
    if constants.CAT_DOWNLOAD_URL in repo_data:
        codemeta_output["downloadUrl"] = repo_data[constants.CAT_DOWNLOAD_URL][0][constants.PROP_RESULT][constants.PROP_VALUE]
    if constants.CAT_NAME in repo_data:
        codemeta_output["name"] = repo_data[constants.CAT_NAME][0][constants.PROP_RESULT][constants.PROP_VALUE]
    if constants.CAT_LOGO in repo_data:
        codemeta_output["logo"] = repo_data[constants.CAT_LOGO][0][constants.PROP_RESULT][constants.PROP_VALUE]
    if constants.CAT_KEYWORDS in repo_data:
        codemeta_output["keywords"] = repo_data[constants.CAT_KEYWORDS][0][constants.PROP_RESULT][constants.PROP_VALUE]
    if constants.CAT_PROGRAMMING_LANGUAGES in repo_data:
        codemeta_output["programmingLanguage"] = [x[constants.PROP_RESULT][constants.PROP_VALUE]
                                                  for x in repo_data[constants.CAT_PROGRAMMING_LANGUAGES]]
    if constants.CAT_REQUIREMENTS in repo_data:
        codemeta_output["softwareRequirements"] = [x[constants.PROP_RESULT]
                                                   [constants.PROP_VALUE] for x in repo_data[constants.CAT_REQUIREMENTS]]
    install_links = []
    if constants.CAT_INSTALLATION in repo_data:
        for inst in repo_data[constants.CAT_INSTALLATION]:
            if inst[constants.PROP_TECHNIQUE] == constants.TECHNIQUE_HEADER_ANALYSIS and constants.PROP_SOURCE in inst.keys():
                install_links.append(inst[constants.PROP_SOURCE])
            elif inst[constants.PROP_TECHNIQUE] == constants.TECHNIQUE_FILE_EXPLORATION:
                install_links.append(
                    inst[constants.PROP_RESULT][constants.PROP_VALUE])
    if constants.CAT_DOCUMENTATION in repo_data:
        for inst in repo_data[constants.CAT_DOCUMENTATION]:
            if inst[constants.PROP_TECHNIQUE] == constants.TECHNIQUE_HEADER_ANALYSIS and constants.PROP_SOURCE in inst.keys():
                install_links.append(inst[constants.PROP_SOURCE])
            elif inst[constants.PROP_TECHNIQUE] == constants.TECHNIQUE_FILE_EXPLORATION or \
                    inst[constants.PROP_TECHNIQUE] == constants.TECHNIQUE_REGULAR_EXPRESSION:
                install_links.append(
                    inst[constants.PROP_RESULT][constants.PROP_VALUE])
    if len(install_links) > 0:
        # remove duplicates and generate codemeta
        install_links = list(set(install_links))
        codemeta_output["buildInstructions"] = install_links
    if constants.CAT_OWNER in repo_data:
        # if user then person, otherwise organization
        type_aux = repo_data[constants.CAT_OWNER][0][constants.PROP_RESULT][constants.PROP_TYPE]
        if type_aux == "User":
            type_aux = "Person"
        codemeta_output["author"] = [
            {
                "@type": type_aux,
                "@id": "https://github.com/" + author_name
            }
        ]
    if constants.CAT_CITATION in repo_data:
        url_cit = []
        for cit in repo_data[constants.CAT_CITATION]:
            if constants.PROP_DOI in cit[constants.PROP_RESULT].keys():
                url_cit.append(cit[constants.PROP_RESULT][constants.PROP_DOI])
            elif constants.PROP_FORMAT in cit[constants.PROP_RESULT].keys() \
                    and cit[constants.PROP_RESULT][constants.PROP_FORMAT] == constants.FORMAT_CFF:
                url_cit.append(cit[constants.PROP_SOURCE])
        if len(url_cit) > 0:
            codemeta_output["citation"] = url_cit
    if constants.CAT_IDENTIFIER in repo_data:
        codemeta_output["identifier"] = repo_data[constants.CAT_IDENTIFIER][0][constants.PROP_RESULT][constants.PROP_VALUE]
    if constants.CAT_README_URL in repo_data:
        codemeta_output["readme"] = repo_data[constants.CAT_README_URL][0][constants.PROP_RESULT][constants.PROP_VALUE]
    # if "contributors" in repo_data:
    #     codemeta_output["contributor"] = data_path(["contributors", "excerpt"])
    # A person is expected, and we extract text at the moment
    if descriptions_text:
        codemeta_output["description"] = descriptions_text
    # if published_date != "":
    # commenting this out because we cannot assume the last published date to be the published date
    #     codemeta_output["datePublished"] = published_date
    pruned_output = {}

    for key, value in codemeta_output.items():
        if not (value is None or ((isinstance(value, list) or isinstance(value, tuple)) and len(value) == 0)):
            pruned_output[key] = value
    # now, prune out the variables that are None
    save_json_output(pruned_output, outfile, None, pretty=pretty)


def create_missing_fields(result):
    """Function to create a small report with the categories SOMEF was not able to find.
    The categories are added to the JSON results. This won't be added if you export TTL or Codemeta"""
    missing = []
    repo_data = result
    for c in constants.categories_files_header:
        if c not in repo_data:
            missing.append(c)
    return missing
