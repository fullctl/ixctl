from django.urls import reverse


def test_view_instance(db, pdb_data, account_objects):

    response = account_objects.client.get(
        reverse("ixctl-home", args=(account_objects.org.slug,))
    )

    assert response.status_code == 200
    assert "ixctl-logo-darkbg.svg" in response.content.decode("utf-8")


def test_view_instance_other(db, pdb_data, account_objects):

    response = account_objects.client.get(
        reverse("ixctl-home", args=(account_objects.other_org.slug,))
    )

    assert response.status_code == 404


def test_view_ixf_export(db, pdb_data, account_objects, client_anon):

    ix = account_objects.ix

    response = account_objects.client.get(
        reverse("ixf export", args=(account_objects.org.slug, ix.urlkey,))
    )

    assert response.status_code == 200

    response = client_anon.get(
        reverse("ixf export", args=(account_objects.org.slug, ix.urlkey,))
    )

    assert response.status_code == 200
