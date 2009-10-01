# Copyright (C) 2007 Samuel Abels, http://debain.org
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
import threading
from Account import Account

class AccountManager(object):
    """
    This class manages a collection of available accounts.
    """

    def __init__(self, accounts = None):
        """
        Constructor.
        """
        self.accounts          = []
        self.unlocked_accounts = []
        self.unlock_cond       = threading.Condition()
        if accounts:
            self.add_account(accounts)


    def add_account(self, accounts):
        """
        Adds one or more account instances to the pool.

        @type  accounts: Account|list[Account]
        @param accounts: The account to be added.
        """
        self.unlock_cond.acquire()
        if isinstance(accounts, Account):
            accounts = [accounts]
        for account in accounts:
            self.accounts.append(account)
            self.unlocked_accounts.append(account)
            account._add_notify(self)
        self.unlock_cond.notify()
        self.unlock_cond.release()


    def get_account_from_name(self, name):
        """
        Returns the account with the given name.

        @type  name: string
        @param name: The name of the account.
        """
        for account in self.accounts:
            if account.get_name() == name:
                return account
        return None


    def n_accounts(self):
        return len(self.accounts)


    def _acquire_specific_account(self, account):
        self.unlock_cond.acquire()
        assert account in self.accounts
        account = account.acquire()
        self.unlock_cond.release()


    def acquire_account(self, account = None):
        """
        Waits until an account becomes available, then locks and returns it.
        If an account is not passed, the next available account is returned.

        @type  account: Account
        @param account: The account to be acquired, or None.
        @rtype:  Account
        @return: The account to be added.
        """
        if account is not None:
            return self._acquire_specific_account(account)
        self.unlock_cond.acquire()
        while len(self.unlocked_accounts) == 0:
            self.unlock_cond.wait()
        account = self.unlocked_accounts[0]
        del self.unlocked_accounts[0]
        account.acquire()
        self.unlock_cond.release()
        return account


    def release_account(self, account):
        """
        Unlocks a previously locked account.

        @type  account: Account
        @param account: The account to be unlocked.
        """
        self.unlock_cond.acquire()
        assert account in self.accounts
        self.unlocked_accounts.append(account)
        self.unlock_cond.notify()
        self.unlock_cond.release()