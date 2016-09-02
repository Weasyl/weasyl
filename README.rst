Welcome to Weasyl!
==================

.. highlight:: console

`Weasyl`_ is a social gallery website designed for artists, writers, musicians,
and more to share their work with other artists and fans. We seek to bring the
creative world together in one easy to use, friendly, community website.


Quickstart
----------

The easiest way to get Weasyl running is within a virtual environment using
`Vagrant`_ (1.6 or greater) with `VirtualBox`_ (4.3.16 or greater). From inside the
``weasyl`` directory, simply run::

  $ make setup-vagrant

After libweasyl is cloned, Vagrant will fetch the base box and then provision
the VM. Expect this step to take a while as it downloads a virtual machine
image, installs all of Weasyl's dependencies, and populates a small database.

To start the server inside the VM, run::

  $ make guest-run

Weasyl will then start running on <https://lo.weasyl.com:8443/>. Ignore any
warnings about the self-signed certificate.


Next Steps
----------

At this point Weasyl is running within a virtual machine. Your Weasyl repo
is mounted as ``/home/vagrant/weasyl`` inside the guest so edits made locally
will be reflected inside the VM. To make changes, stop the ``make guest-run``
process, edit the code, and rerun ``make guest-run``.

If you need to examine the virtual machine (e.g. to look at the database
directly), run ``vagrant ssh``.


The Sample Database
-------------------

The downloaded database contains sample content pulled and scrubbed from
Weasyl staff accounts. No content should be included from non-staff users
or those who haven't otherwise explicitly given permission to use their
account.

For privacy and technical reasons, not all content is included: Hidden
submissions, private messages, journals, hidden favorites, notifications,
and similar things have been removed. If you want to develop around such
functionality, they will have to be added manually.

All passwords in the database have been set to 'password'.


Troubleshooting and Getting Help
--------------------------------

If the ``make setup-vagrant`` step fails halfway through, you can resume it with the
standard vagrant commands ``vagrant up`` followed by ``vagrant provision``.

If you have questions or get stuck, you can trying talking to Weasyl project members in
the project's `gitter room <https://gitter.im/Weasyl/weasyl>`_.

The above instructions have been tested on Linux and OS X. It should be possible
to run Weasyl in a virtual environment under Windows, but it hasn't been thoroughly
tested.

When developing under Windows hosts with a Linux guest, ensure that either Intel VT-x/EPT
or AMD-V/RVI are exposed to the virtual machine (e.g., the "Virtualize Intel VT-x/EPT or
AMD-V/RVI" setting under the Processors device settings for the guest VM in VMware). If
this setting is not selected, the configuration of the Weasyl VM via ``make setup-vagrant``
may hang when Vagrant attempts to SSH to the VM to perform configuration of the guest.


Code of Conduct
---------------

Please note that this project is released with a `Contributor Code of Conduct`_. By
participating in this project you agree to abide by its terms.


Style Guide
-----------

When committing code, be sure to follow the `Style and Best Practices Guide`_.


.. _Weasyl: https://www.weasyl.com
.. _Vagrant: https://www.vagrantup.com
.. _VirtualBox: https://www.virtualbox.org
.. _Contributor Code of Conduct: CODE_OF_CONDUCT.md
.. _Style and Best Practices Guide: STYLE_GUIDE.md
